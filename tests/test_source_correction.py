from __future__ import annotations

import copy
import hashlib
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

import scripts.source_correction as source_correction
import scripts.verify_migration as verify_migration
from scripts.source_correction import (
    ARTICLE_PATH,
    MEDIA_NEW_PATH,
    MEDIA_OLD_PATH,
    PODCAST_PATH,
    SourceCorrectionError,
    apply_article_url_corrections,
    sha256_file,
    validate_source_correction,
)
from scripts.verify_migration import verify_media_overlay, verify_podcast_metadata_overlay

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / source_correction.MANIFEST_RELATIVE_PATH


def _manifest() -> dict[str, Any]:
    value = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_manifest(path: Path, value: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _legacy_article_bytes() -> bytes:
    current = (ROOT / ARTICLE_PATH).read_text(encoding="utf-8")
    path_new = "https://aishippingblog.com/p/ai-native-development-specifications"
    path_old = "https://alexeyondata.substack.com/p/ai-native-development-specifications"
    home_new = "https://aishippingblog.com/"
    home_old = "https://alexeyondata.substack.com/"
    # The path URL is replaced first because the home URL is its prefix.
    legacy = current.replace(path_new, path_old).replace(home_new, home_old)
    result = legacy.encode("utf-8")
    assert hashlib.sha256(result).hexdigest() == source_correction.ARTICLE_LEGACY_SHA256
    return result


def _copy_contract_targets(destination: Path) -> None:
    for relative in (
        "migration.yaml",
        source_correction.MANIFEST_RELATIVE_PATH.as_posix(),
        ARTICLE_PATH,
        PODCAST_PATH,
        MEDIA_NEW_PATH,
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def test_source_correction_manifest_is_valid_and_exact() -> None:
    summary = validate_source_correction(ROOT)

    assert summary["replacement_count"] == 5
    assert summary["manifest_sha256"] == source_correction.EXPECTED_MANIFEST_SHA256
    assert tuple(summary["article_corrections"]) == (ARTICLE_PATH,)
    assert tuple(summary["podcast_corrections"]) == (PODCAST_PATH,)
    assert tuple(summary["media_renames"]) == (MEDIA_OLD_PATH,)


def test_article_correction_replaces_complete_destinations_only() -> None:
    row = validate_source_correction(ROOT)["article_corrections"][ARTICLE_PATH]
    legacy = _legacy_article_bytes()
    text = legacy.decode("utf-8")

    assert text.count("https://alexeyondata.substack.com/") == 5
    assert (
        len(
            source_correction._link_matches(
                text,
                "markdown_destination",
                "https://alexeyondata.substack.com/",
            )
        )
        == 1
    )
    assert (
        len(
            source_correction._link_matches(
                text,
                "html_href",
                "https://alexeyondata.substack.com/",
            )
        )
        == 1
    )

    corrected = apply_article_url_corrections(legacy, row)
    assert corrected == (ROOT / ARTICLE_PATH).read_bytes()


@pytest.mark.parametrize(
    ("path", "replacement", "message"),
    (
        (("replacement_count",), 6, "replacement count"),
        (("articles", 0, "replacements", 0, "match"), "unbounded", "match kind"),
        (("articles", 0, "replacements", 0, "occurrences"), 3, "occurrence"),
        (("articles", 0, "replacements", 0, "line_numbers"), [137], "line"),
        (("media_renames", 0, "new_path"), "images/podcast/other.jpg", "new_path"),
    ),
)
def test_manifest_rejects_contract_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str | int, ...],
    replacement: Any,
    message: str,
) -> None:
    candidate_manifest = tmp_path / source_correction.MANIFEST_RELATIVE_PATH
    candidate_manifest.parent.mkdir(parents=True)
    value = copy.deepcopy(_manifest())
    current: Any = value
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = replacement
    _write_manifest(candidate_manifest, value)

    monkeypatch.setattr(
        source_correction,
        "EXPECTED_MANIFEST_SHA256",
        sha256_file(candidate_manifest),
    )
    with pytest.raises(SourceCorrectionError, match=message):
        validate_source_correction(ROOT, candidate_manifest)


def test_manifest_rejects_target_byte_drift(tmp_path: Path) -> None:
    candidate = tmp_path / "repository"
    _copy_contract_targets(candidate)
    article = candidate / ARTICLE_PATH
    article.write_bytes(article.read_bytes() + b"\nundeclared\n")

    with pytest.raises(SourceCorrectionError, match="article 1: target digest differs"):
        validate_source_correction(candidate)


def test_manifest_rejects_old_media_path_and_unbounded_rename(tmp_path: Path) -> None:
    candidate = tmp_path / "repository"
    _copy_contract_targets(candidate)
    old_path = candidate / MEDIA_OLD_PATH
    old_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / MEDIA_NEW_PATH, old_path)

    with pytest.raises(SourceCorrectionError, match="old media path still exists"):
        validate_source_correction(candidate)


def test_podcast_overlay_allows_only_declared_image_scalar() -> None:
    row = validate_source_correction(ROOT)["podcast_corrections"][PODCAST_PATH]
    expected = {"image": row["old"], "title": "unchanged"}
    actual = {"image": row["new"], "title": "unchanged"}

    verify_podcast_metadata_overlay(
        expected,
        actual,
        PODCAST_PATH,
        {},
        {PODCAST_PATH: row},
    )
    with pytest.raises(ValueError, match="source correction value differs"):
        verify_podcast_metadata_overlay(
            expected,
            {**actual, "image": row["old"]},
            PODCAST_PATH,
            {},
            {PODCAST_PATH: row},
        )


def test_media_overlay_accepts_only_lossless_declared_rename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    for root in (source, target):
        (root / "images/podcast").mkdir(parents=True)
    source_old = source / MEDIA_OLD_PATH
    target_new = target / MEDIA_NEW_PATH
    source_old.write_bytes(b"lossless")
    target_new.write_bytes(b"lossless")
    renames = {MEDIA_OLD_PATH: {"new_path": MEDIA_NEW_PATH}}
    monkeypatch.setattr(verify_migration, "EXPECTED_REPAIRS", ())

    assert verify_media_overlay(source, target, set(), renames) == (1, 1)

    (target / MEDIA_OLD_PATH).write_bytes(b"lossless")
    with pytest.raises(ValueError, match="file set differs"):
        verify_media_overlay(source, target, set(), renames)


def test_source_attestation_requires_clean_matching_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    head = source_correction._git_revision(ROOT, "HEAD")
    monkeypatch.setattr(source_correction, "_git_checkout_is_dirty", lambda root: True)
    with pytest.raises(SourceCorrectionError, match="checkout is dirty"):
        source_correction.emit_source_correction_attestation(ROOT, head)


def test_source_attestation_binds_tree_diff_and_complete_corrections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    head = source_correction._git_revision(ROOT, "HEAD")
    tree = "a" * 40
    monkeypatch.setattr(source_correction, "_git_checkout_is_dirty", lambda root: False)
    monkeypatch.setattr(
        source_correction,
        "_git_revision",
        lambda root, revision: head if revision == "HEAD" else tree,
    )
    monkeypatch.setattr(
        source_correction,
        "_git_changed_paths",
        lambda root: source_correction.EXPECTED_CHANGED_PATHS,
    )

    attestation = source_correction.emit_source_correction_attestation(ROOT, head)

    assert attestation["replacement_tree"] == tree
    assert len(attestation["changed_paths"]) == 11
    assert attestation["corrections"]["articles"][0]["replacement_count"] == 5
    assert attestation["corrections"]["podcasts"][0]["field"] == "image"
    assert attestation["corrections"]["media_renames"][0]["bytes"] == 38743
