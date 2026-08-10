from __future__ import annotations

import copy
import hashlib
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

import scripts.editorial_overlay as editorial_overlay
from scripts.editorial_overlay import (
    EXPECTED_MANIFEST_SHA256,
    EXPECTED_TARGETS,
    EditorialOverlayError,
    sha256_file,
    validate_editorial_overlay,
)
from scripts.verify_migration import verify_podcast_metadata_overlay

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / editorial_overlay.MANIFEST_RELATIVE_PATH


def _manifest() -> dict[str, Any]:
    value = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _candidate_repository(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    candidate = tmp_path / "repository"
    candidate.mkdir()
    shutil.copy2(ROOT / "migration.yaml", candidate / "migration.yaml")
    candidate_manifest = candidate / editorial_overlay.MANIFEST_RELATIVE_PATH
    candidate_manifest.parent.mkdir(parents=True)
    shutil.copy2(MANIFEST, candidate_manifest)
    for relative in EXPECTED_TARGETS:
        destination = candidate / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    return candidate, _manifest()


def _pin_manifest(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    monkeypatch.setattr(editorial_overlay, "EXPECTED_MANIFEST_SHA256", sha256_file(path))


def _set_nested(value: Any, path: tuple[str | int, ...], replacement: Any) -> None:
    current = value
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = replacement


def test_checked_editorial_overlay_is_valid_and_exact() -> None:
    summary = validate_editorial_overlay(ROOT)

    assert summary["targets"] == 19
    assert summary["field"] == "description"
    assert summary["source_commit"] == editorial_overlay.SOURCE_COMMIT
    assert summary["manifest_sha256"] == EXPECTED_MANIFEST_SHA256
    assert tuple(summary["descriptions"]) == EXPECTED_TARGETS


def test_editorial_overlay_manifest_bytes_are_pinned(tmp_path: Path) -> None:
    candidate = tmp_path / "overlay.yaml"
    candidate.write_bytes(MANIFEST.read_bytes() + b"\n")

    with pytest.raises(EditorialOverlayError, match="manifest bytes differ"):
        validate_editorial_overlay(ROOT, candidate)


@pytest.mark.parametrize(
    ("path", "replacement", "message"),
    (
        (("schema_version",), 2, "schema_version"),
        (("schema_version",), True, "schema_version"),
        (("issue",), "https://example.test/3", "issue URL"),
        (("created",), "2026-08-11", "creation date"),
        (("baseline_content_commit",), "0" * 40, "baseline content commit"),
        (("source", "repository"), "https://example.test/source", "source repository"),
        (("source", "commit"), "0" * 40, "source commit"),
        (("migration", "manifest"), "other.yaml", "migration manifest path"),
        (("migration", "sha256"), "0" * 64, "migration manifest digest"),
        (("field",), "title", "overlay field"),
        (("target_count",), 20, "target count"),
        (("targets", 0, "key"), "title", "key must be description"),
        (("targets", 0, "description_sha256"), "invalid", "description_sha256 is invalid"),
        (("targets", 0, "target_sha256"), "invalid", "target_sha256 is invalid"),
    ),
)
def test_rejects_pinned_contract_field_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str | int, ...],
    replacement: Any,
    message: str,
) -> None:
    manifest = copy.deepcopy(_manifest())
    _set_nested(manifest, path, replacement)
    candidate = tmp_path / "overlay.yaml"
    _write_manifest(candidate, manifest)
    _pin_manifest(monkeypatch, candidate)

    with pytest.raises(EditorialOverlayError, match=message):
        validate_editorial_overlay(ROOT, candidate)


@pytest.mark.parametrize("location", ("top", "source", "migration", "target"))
def test_rejects_malformed_schema_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    location: str,
) -> None:
    manifest = copy.deepcopy(_manifest())
    if location == "top":
        manifest["unexpected"] = True
    elif location == "source":
        manifest["source"]["unexpected"] = True
    elif location == "migration":
        manifest["migration"]["unexpected"] = True
    else:
        manifest["targets"][0]["unexpected"] = True
    candidate = tmp_path / "overlay.yaml"
    _write_manifest(candidate, manifest)
    _pin_manifest(monkeypatch, candidate)

    with pytest.raises(EditorialOverlayError, match="schema keys differ"):
        validate_editorial_overlay(ROOT, candidate)


@pytest.mark.parametrize("mutation", ("missing", "extra", "duplicate"))
def test_rejects_missing_extra_or_duplicate_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    manifest = copy.deepcopy(_manifest())
    if mutation == "missing":
        manifest["targets"].pop()
    elif mutation == "extra":
        manifest["targets"].append(copy.deepcopy(manifest["targets"][0]))
    else:
        manifest["targets"][-1] = copy.deepcopy(manifest["targets"][0])
    candidate = tmp_path / "overlay.yaml"
    _write_manifest(candidate, manifest)
    _pin_manifest(monkeypatch, candidate)

    message = "target row count differs" if mutation != "duplicate" else "duplicate target path"
    with pytest.raises(EditorialOverlayError, match=message):
        validate_editorial_overlay(ROOT, candidate)


@pytest.mark.parametrize(
    "path",
    (
        "../podcasts/_s12e08.yaml",
        "podcasts/../_s12e08.yaml",
        "podcasts//_s12e08.yaml",
        "podcasts/./_s12e08.yaml",
        "/podcasts/_s12e08.yaml",
        r"podcasts\_s12e08.yaml",
        "podcasts/_s12e08.yml",
    ),
)
def test_rejects_traversal_and_noncanonical_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
) -> None:
    manifest = copy.deepcopy(_manifest())
    manifest["targets"][0]["path"] = path
    candidate = tmp_path / "overlay.yaml"
    _write_manifest(candidate, manifest)
    _pin_manifest(monkeypatch, candidate)

    with pytest.raises(EditorialOverlayError, match="target path is not canonical"):
        validate_editorial_overlay(ROOT, candidate)


def test_rejects_description_and_target_content_drift(tmp_path: Path) -> None:
    candidate, _ = _candidate_repository(tmp_path)
    target = candidate / EXPECTED_TARGETS[0]
    current = target.read_text(encoding="utf-8")
    target.write_text(
        current.replace("description: Jekaterina", "description: Changed", 1),
        encoding="utf-8",
    )

    with pytest.raises(EditorialOverlayError, match="description digest differs"):
        validate_editorial_overlay(candidate)

    shutil.copy2(ROOT / EXPECTED_TARGETS[0], target)
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(EditorialOverlayError, match="target content digest differs"):
        validate_editorial_overlay(candidate)


def test_rejects_missing_and_symlinked_targets(tmp_path: Path) -> None:
    candidate, _ = _candidate_repository(tmp_path)
    target = candidate / EXPECTED_TARGETS[0]
    target.unlink()
    with pytest.raises(EditorialOverlayError, match="target file is missing"):
        validate_editorial_overlay(candidate)

    target.symlink_to(ROOT / EXPECTED_TARGETS[0])
    with pytest.raises(EditorialOverlayError, match="target is a symlink"):
        validate_editorial_overlay(candidate)


def test_rejects_non_string_description_even_with_updated_file_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate, manifest = _candidate_repository(tmp_path)
    target = candidate / EXPECTED_TARGETS[0]
    metadata = yaml.safe_load(target.read_text(encoding="utf-8"))
    metadata["description"] = ["not", "a", "scalar"]
    target.write_text(
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    manifest["targets"][0]["target_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest_path = candidate / editorial_overlay.MANIFEST_RELATIVE_PATH
    _write_manifest(manifest_path, manifest)
    _pin_manifest(monkeypatch, manifest_path)

    with pytest.raises(EditorialOverlayError, match="description must be a non-empty string"):
        validate_editorial_overlay(candidate)


def test_source_comparison_allows_only_the_declared_description() -> None:
    relative = EXPECTED_TARGETS[0]
    expected = {"slug": "episode", "title": "Original"}
    overlay = {relative: "Declared description"}

    verify_podcast_metadata_overlay(
        expected,
        {**expected, "description": "Declared description"},
        relative,
        overlay,
    )

    with pytest.raises(ValueError, match="migrated podcast metadata differs"):
        verify_podcast_metadata_overlay(
            expected,
            {**expected, "title": "Changed", "description": "Declared description"},
            relative,
            overlay,
        )
    with pytest.raises(ValueError, match="declared podcast description differs"):
        verify_podcast_metadata_overlay(
            expected,
            {**expected, "description": "Changed"},
            relative,
            overlay,
        )
    with pytest.raises(ValueError, match="migrated podcast metadata differs"):
        verify_podcast_metadata_overlay(
            expected,
            {**expected, "description": "Undeclared"},
            "podcasts/not-declared.yaml",
            overlay,
        )
