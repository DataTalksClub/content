from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import scripts.migrate_legacy_content as migrate_legacy_content
from scripts.removal_manifest import (
    CURRENT_COUNTS,
    EXPECTED_MANIFEST_SHA256,
    EXPECTED_REMOVALS,
    RemovalManifestError,
    removal_source_paths,
    validate_removal_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "migration/podcast-removals.yaml"


def test_checked_removal_manifest_is_exact() -> None:
    summary = validate_removal_manifest(ROOT)

    assert summary["removals"] == 2
    assert summary["current_counts"] == CURRENT_COUNTS
    assert summary["manifest_sha256"] == EXPECTED_MANIFEST_SHA256
    assert removal_source_paths(MANIFEST) == frozenset(row["source"] for row in EXPECTED_REMOVALS)


def test_validator_rejects_a_reintroduced_removed_record(tmp_path: Path) -> None:
    candidate = tmp_path / "repository"
    shutil.copytree(ROOT / "podcasts", candidate / "podcasts")
    (candidate / "migration").mkdir()
    shutil.copy2(ROOT / "migration/migration.yaml", candidate / "migration/migration.yaml")
    shutil.copy2(MANIFEST, candidate / MANIFEST.relative_to(ROOT))
    (candidate / "podcasts/s01/e01.yaml").write_text("slug: _s12e08\n", encoding="utf-8")

    with pytest.raises(RemovalManifestError, match="removed podcast is present"):
        validate_removal_manifest(candidate)


def test_importer_excludes_declared_legacy_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "legacy"
    target = tmp_path / "target"
    for relative in (
        "_posts",
        "_books",
        "_podcast",
        "images/posts",
        "images/podcast",
        "images/books",
    ):
        (source / relative).mkdir(parents=True)

    for slug in (
        "_s12e08",
        "_theme-park-crowd-modeling-to-tesla-full-stack-data-engineering",
    ):
        (source / "_podcast" / f"{slug}.md").write_text("not imported\n", encoding="utf-8")
    (source / "_podcast/retained.md").write_text(
        "---\ntitle: Retained\nseason: 1\nepisode: 1\n---\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        migrate_legacy_content.subprocess,
        "run",
        lambda *args, **kwargs: type("Result", (), {"stdout": "0" * 40})(),
    )

    provenance = migrate_legacy_content.migrate(source, target, "2026-09-01")

    assert provenance["counts"]["podcasts"] == 1
    assert (target / "podcasts/s01/e01.yaml").is_file()
    assert not list((target / "podcasts").rglob("*_s12e08*"))
    assert not list(
        (target / "podcasts").rglob(
            "*theme-park-crowd-modeling-to-tesla-full-stack-data-engineering*"
        )
    )
