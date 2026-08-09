from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

import scripts.repair_manifest as repair_manifest
from scripts.repair_manifest import (
    EXPECTED_COUNTS,
    EXPECTED_MANIFEST_SHA256,
    EXPECTED_REPAIRS,
    MIGRATION_MANIFEST_SHA256,
    RepairManifestError,
    emit_attestation,
    sha256_file,
    validate_repair_manifest,
)
from scripts.verify_migration import verify_article_overlay, verify_media_overlay

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "repairs/2026-08-09-missing-media.yaml"
ADDED_REPAIR_PATHS = tuple(str(row["result"]) for row in EXPECTED_REPAIRS if row["added"])
CORRECTED_RECORDS = tuple(row for row in EXPECTED_REPAIRS if row["action"] == "correct_image_path")


def _manifest() -> dict[str, Any]:
    value = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")


def _candidate_repository(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    candidate_root = tmp_path / "repository"
    candidate_root.mkdir()
    shutil.copy2(ROOT / "migration.yaml", candidate_root / "migration.yaml")
    (candidate_root / repair_manifest.MANIFEST_RELATIVE_PATH).parent.mkdir(parents=True)
    shutil.copy2(MANIFEST, candidate_root / repair_manifest.MANIFEST_RELATIVE_PATH)
    manifest = _manifest()
    for row in manifest["repairs"]:
        for relative in (row["record"], row["result"]["path"]):
            destination = candidate_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
    return candidate_root, manifest


def _set_nested(value: Any, path: tuple[str | int, ...], replacement: Any) -> None:
    current = value
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = replacement


def test_checked_repair_manifest_is_valid_and_exact() -> None:
    summary = validate_repair_manifest(ROOT)

    assert summary == {
        "repairs": 10,
        "added_media": 8,
        "media": 815,
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
    }
    assert sha256_file(ROOT / "migration.yaml") == MIGRATION_MANIFEST_SHA256


def test_attestation_is_deterministic_and_binds_replacement_commit() -> None:
    commit = "1" * 40

    first = emit_attestation(ROOT, commit)
    second = emit_attestation(ROOT, commit)

    assert first == second
    assert first["replacement_commit"] == commit
    assert first["repair_manifest_sha256"] == EXPECTED_MANIFEST_SHA256
    assert first["counts"] == EXPECTED_COUNTS
    assert json.dumps(first, indent=2, sort_keys=True) == json.dumps(
        second,
        indent=2,
        sort_keys=True,
    )


@pytest.mark.parametrize("commit", ("", "ABC" * 13 + "A", "g" * 40, "1" * 39))
def test_attestation_rejects_invalid_replacement_commit(commit: str) -> None:
    with pytest.raises(RepairManifestError, match="replacement commit"):
        emit_attestation(ROOT, commit)


@pytest.mark.parametrize(
    ("path", "replacement"),
    (
        (("expected_delta", "media"), 9),
        (("current_counts", "media"), 816),
        (("invariants", 0), "migration provenance may change"),
        (("generation", "shared_inputs", "styles", "blob"), "0" * 40),
        (("generation", "renderers", "post", "template_sha256"), "0" * 64),
        (("generation", "toolchain", "node"), "v99.0.0"),
        (("generation", "toolchain", "chromium", "command"), "other-browser"),
        (("generation", "external_resources", "google_font_css"), "HTTP 500"),
        (("repairs", 0, "baseline_sha256"), "0" * 64),
        (("repairs", 0, "source_history", "rename_commit"), "0" * 40),
        (("repairs", 1, "generator_inputs", "portrait_blob"), "0" * 40),
        (("repairs", 1, "command"), "node unpinned.js"),
        (("repairs", 6, "evidence_commit"), "0" * 40),
        (("repairs", 1, "editor_approval", "comment_url"), "https://example.test"),
        (("repairs", 1, "editor_approval", "verdict"), "REJECT"),
    ),
)
def test_every_provenance_class_is_pinned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str | int, ...],
    replacement: Any,
) -> None:
    manifest = copy.deepcopy(_manifest())
    _set_nested(manifest, path, replacement)
    candidate = tmp_path / "repair.yaml"
    _write_manifest(candidate, manifest)
    monkeypatch.setattr(
        repair_manifest,
        "EXPECTED_MANIFEST_SHA256",
        sha256_file(candidate),
    )

    with pytest.raises(RepairManifestError):
        validate_repair_manifest(ROOT, candidate)


def test_editor_digest_has_independent_trust_root_when_asset_and_manifest_change_together(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_root, manifest = _candidate_repository(tmp_path)

    row = manifest["repairs"][1]
    asset = candidate_root / row["result"]["path"]
    original = asset.read_bytes()
    mutated = original[:-10] + bytes([original[-10] ^ 1]) + original[-9:]
    asset.unlink()
    asset.write_bytes(mutated)
    mutated_sha = hashlib.sha256(mutated).hexdigest()
    row["result"]["sha256"] = mutated_sha
    row["editor_approval"]["output_sha256"] = mutated_sha
    manifest_path = candidate_root / repair_manifest.MANIFEST_RELATIVE_PATH
    _write_manifest(manifest_path, manifest)

    monkeypatch.setattr(
        repair_manifest,
        "EXPECTED_MANIFEST_SHA256",
        sha256_file(manifest_path),
    )
    replacement_repairs = list(EXPECTED_REPAIRS)
    replacement_row = dict(replacement_repairs[1])
    replacement_row["row_digest"] = repair_manifest._canonical_digest(row)
    replacement_repairs[1] = replacement_row
    monkeypatch.setattr(repair_manifest, "EXPECTED_REPAIRS", tuple(replacement_repairs))
    monkeypatch.setattr(repair_manifest, "_validate_repository_counts", lambda root: None)

    with pytest.raises(RepairManifestError, match="editor-approved digest"):
        validate_repair_manifest(candidate_root)


@pytest.mark.parametrize("relative", ADDED_REPAIR_PATHS)
def test_each_added_repair_asset_is_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
) -> None:
    candidate_root, _ = _candidate_repository(tmp_path)
    (candidate_root / relative).unlink()
    monkeypatch.setattr(repair_manifest, "_validate_repository_counts", lambda root: None)

    with pytest.raises(RepairManifestError, match="result file is missing"):
        validate_repair_manifest(candidate_root)


@pytest.mark.parametrize("relative", ADDED_REPAIR_PATHS)
def test_each_added_repair_asset_hash_is_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
) -> None:
    candidate_root, _ = _candidate_repository(tmp_path)
    asset = candidate_root / relative
    original = asset.read_bytes()
    asset.write_bytes(original[:-3] + bytes([original[-3] ^ 1]) + original[-2:])
    monkeypatch.setattr(repair_manifest, "_validate_repository_counts", lambda root: None)

    with pytest.raises(RepairManifestError, match="digest differs"):
        validate_repair_manifest(candidate_root)


@pytest.mark.parametrize("row", CORRECTED_RECORDS, ids=lambda row: Path(row["record"]).name)
def test_each_corrected_article_image_scalar_is_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    row: dict[str, Any],
) -> None:
    candidate_root, _ = _candidate_repository(tmp_path)
    article = candidate_root / str(row["record"])
    current = article.read_text(encoding="utf-8")
    new_line = f"image: {row['new_value']}"
    old_line = f"image: {row['old_value']}"
    assert current.count(new_line) == 1
    article.write_text(current.replace(new_line, old_line, 1), encoding="utf-8")
    monkeypatch.setattr(repair_manifest, "_validate_repository_counts", lambda root: None)

    with pytest.raises(RepairManifestError, match="corrected image value differs"):
        validate_repair_manifest(candidate_root)


def test_article_overlay_allows_only_the_two_exact_scalar_changes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (target / "articles").mkdir(parents=True)
    correction_rows: dict[str, dict[str, Any]] = {}
    article_sources: list[Path] = []
    for row in EXPECTED_REPAIRS:
        if row["action"] != "correct_image_path":
            continue
        name = Path(str(row["record"])).name
        legacy = source / name
        legacy.write_text(
            f"---\ntitle: Exact\nimage: {row['old_value']}\n---\n\nUnchanged body.\n",
            encoding="utf-8",
        )
        (target / "articles" / name).write_text(
            f"---\ntitle: Exact\nimage: {row['new_value']}\n---\n\nUnchanged body.\n",
            encoding="utf-8",
        )
        article_sources.append(legacy)
        correction_rows[str(row["record"])] = {
            "old_value": row["old_value"],
            "new_value": row["new_value"],
        }

    verify_article_overlay(article_sources, target, correction_rows)

    changed = target / str(EXPECTED_REPAIRS[6]["record"])
    changed.write_text(changed.read_text(encoding="utf-8") + "Changed body.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="article bytes differ"):
        verify_article_overlay(article_sources, target, correction_rows)


def test_media_overlay_rejects_changed_baseline_and_unmanifested_addition(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    for root in (source, target):
        for category in ("posts", "podcast", "books"):
            (root / "images" / category).mkdir(parents=True)
    baseline = "images/posts/baseline.jpg"
    (source / baseline).write_bytes(b"baseline")
    (target / baseline).write_bytes(b"baseline")
    additions = {str(row["result"]) for row in EXPECTED_REPAIRS if row["added"]}
    for relative in additions:
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"repair")

    assert verify_media_overlay(source, target, additions) == (1, 9)

    (target / baseline).write_bytes(b"changed")
    with pytest.raises(ValueError, match="migrated bytes differ"):
        verify_media_overlay(source, target, additions)
    (target / baseline).write_bytes(b"baseline")
    (target / "images/posts/unmanifested.jpg").write_bytes(b"extra")
    with pytest.raises(ValueError, match="file set differs"):
        verify_media_overlay(source, target, additions)
