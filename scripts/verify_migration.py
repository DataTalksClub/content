from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml

from scripts.migrate_legacy_content import (
    read_legacy_document,
    resources_from_body,
    slug_for,
)


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> bytes:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.digest()


def verify_migration(source: Path, target: Path) -> dict[str, int]:
    provenance = load_yaml(target / "migration.yaml")
    source_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if provenance["source"]["revision"] != source_revision:
        raise ValueError("legacy checkout revision does not match migration.yaml")

    article_sources = sorted((source / "_posts").glob("*.md"))
    for legacy in article_sources:
        if legacy.read_bytes() != (target / "articles" / legacy.name).read_bytes():
            raise ValueError(f"{legacy}: migrated article bytes differ")

    podcast_sources = sorted(
        path for path in (source / "_podcast").glob("*.md") if path.name != "_template.md"
    )
    transcript_count = 0
    for legacy in podcast_sources:
        metadata, body, prefix = read_legacy_document(legacy)
        transcript = metadata.pop("transcript", None)
        slug = slug_for(legacy)
        expected: dict[str, Any] = {
            "slug": slug,
            "legacy_path": f"/podcast/{slug}.html",
            **metadata,
        }
        if prefix:
            expected["legacy_prefix"] = prefix
        if transcript is not None:
            expected["transcript"] = f"transcripts/{slug}.yaml"
            actual_transcript = load_yaml(target / "podcasts" / "transcripts" / f"{slug}.yaml")
            if actual_transcript != {"podcast": slug, "segments": transcript}:
                raise ValueError(f"{legacy}: migrated transcript differs")
            transcript_count += 1
        if body:
            resources = resources_from_body(body)
            if resources is None:
                expected["notes"] = body
            else:
                expected["resources"] = resources
        if load_yaml(target / "podcasts" / f"{slug}.yaml") != expected:
            raise ValueError(f"{legacy}: migrated podcast metadata differs")

    book_sources = sorted(
        path for path in (source / "_books").glob("*.md") if path.name != "_template.md"
    )
    for legacy in book_sources:
        metadata, body, prefix = read_legacy_document(legacy)
        if prefix:
            raise ValueError(f"{legacy}: unexpected book prefix")
        slug = slug_for(legacy)
        expected = {
            "slug": slug,
            "legacy_path": f"/books/{slug}.html",
            **metadata,
            "summary": body,
        }
        if load_yaml(target / "books" / f"{slug}.yaml") != expected:
            raise ValueError(f"{legacy}: migrated book metadata differs")

    image_count = 0
    for category in ("posts", "podcast", "books"):
        source_root = source / "images" / category
        target_root = target / "images" / category
        source_files = sorted(
            path.relative_to(source_root) for path in source_root.rglob("*") if path.is_file()
        )
        target_files = sorted(
            path.relative_to(target_root) for path in target_root.rglob("*") if path.is_file()
        )
        if source_files != target_files:
            raise ValueError(f"images/{category}: migrated file set differs")
        for relative in source_files:
            if sha256(source_root / relative) != sha256(target_root / relative):
                raise ValueError(f"images/{category}/{relative}: migrated bytes differ")
        image_count += len(source_files)

    counts = {
        "articles": len(article_sources),
        "podcasts": len(podcast_sources),
        "transcripts": transcript_count,
        "books": len(book_sources),
        "images": image_count,
    }
    expected_counts = provenance["counts"]
    if counts["articles"] != expected_counts["articles"]:
        raise ValueError("article count differs from migration.yaml")
    if counts["podcasts"] != expected_counts["podcasts"]:
        raise ValueError("podcast count differs from migration.yaml")
    if counts["transcripts"] != expected_counts["podcast_transcripts"]:
        raise ValueError("transcript count differs from migration.yaml")
    if counts["books"] != expected_counts["books"]:
        raise ValueError("book count differs from migration.yaml")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the migrated content against its source")
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--target",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()
    try:
        counts = verify_migration(args.source.resolve(), args.target.resolve())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"STOP: {error}")
        return 1
    rendered = ", ".join(f"{name}={count}" for name, count in counts.items())
    print(f"PASS: {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
