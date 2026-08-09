from __future__ import annotations

import argparse
import hashlib
import stat
import subprocess
from pathlib import Path
from typing import Any

import yaml

from scripts.migrate_legacy_content import (
    read_legacy_document,
    resources_from_body,
    slug_for,
)
from scripts.repair_manifest import (
    EXPECTED_COUNTS,
    EXPECTED_REPAIRS,
    LEGACY_COMMIT,
    load_repair_manifest,
    validate_repair_manifest,
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
    repair_summary = validate_repair_manifest(target)
    repairs = load_repair_manifest(target / "repairs/2026-08-09-missing-media.yaml")
    provenance = load_yaml(target / "migration.yaml")
    source_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if source_revision != LEGACY_COMMIT or provenance["source"]["revision"] != source_revision:
        raise ValueError("legacy checkout revision does not match migration.yaml")

    article_sources = sorted((source / "_posts").glob("*.md"))
    correction_rows = {
        str(row["record"]): row
        for row in repairs["repairs"]
        if row["action"] == "correct_image_path"
    }
    verify_article_overlay(article_sources, target, correction_rows)

    podcast_sources = sorted(
        path for path in (source / "_podcast").glob("*.md") if path.name != "_template.md"
    )
    expected_podcast_names = {f"{slug_for(path)}.yaml" for path in podcast_sources}
    actual_podcast_names = {path.name for path in (target / "podcasts").glob("*.yaml")}
    if actual_podcast_names != expected_podcast_names:
        raise ValueError("podcasts: migrated file set differs")
    transcript_count = 0
    expected_transcript_names: set[str] = set()
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
            expected_transcript_names.add(f"{slug}.yaml")
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
            raise ValueError(f"podcasts/{slug}.yaml: migrated podcast metadata differs")

    actual_transcript_names = {
        path.name for path in (target / "podcasts/transcripts").glob("*.yaml")
    }
    if actual_transcript_names != expected_transcript_names:
        raise ValueError("podcasts/transcripts: migrated file set differs")

    book_sources = sorted(
        path for path in (source / "_books").glob("*.md") if path.name != "_template.md"
    )
    expected_book_names = {f"{slug_for(path)}.yaml" for path in book_sources}
    actual_book_names = {path.name for path in (target / "books").glob("*.yaml")}
    if actual_book_names != expected_book_names:
        raise ValueError("books: migrated file set differs")
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
            raise ValueError(f"books/{slug}.yaml: migrated book metadata differs")

    added_media = {
        str(row["result"]["path"]) for row in repairs["repairs"] if row["result"]["added"]
    }
    baseline_image_count, image_count = verify_media_overlay(source, target, added_media)

    counts = {
        "articles": len(article_sources),
        "podcasts": len(podcast_sources),
        "transcripts": transcript_count,
        "books": len(book_sources),
        "images": image_count,
        "baseline_images": baseline_image_count,
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
    if counts["baseline_images"] != EXPECTED_COUNTS["media"] - repair_summary["added_media"]:
        raise ValueError("baseline media count differs from repair manifest")
    if counts["images"] != EXPECTED_COUNTS["media"]:
        raise ValueError("repaired media count differs from repair manifest")
    return counts


def verify_article_overlay(
    article_sources: list[Path],
    target: Path,
    correction_rows: dict[str, dict[str, Any]],
) -> None:
    expected_names = {path.name for path in article_sources}
    actual_names = {path.name for path in (target / "articles").glob("*.md")}
    if actual_names != expected_names:
        raise ValueError("articles: migrated file set differs")
    expected_corrections = {
        str(row["record"]) for row in EXPECTED_REPAIRS if row["action"] == "correct_image_path"
    }
    if set(correction_rows) != expected_corrections:
        raise ValueError("articles: correction row set differs")

    for legacy in article_sources:
        relative = f"articles/{legacy.name}"
        source_bytes = legacy.read_bytes()
        expected_bytes = source_bytes
        row = correction_rows.get(relative)
        if row is not None:
            old_line = f"image: {row['old_value']}\n".encode()
            new_line = f"image: {row['new_value']}\n".encode()
            if source_bytes.count(old_line) != 1:
                raise ValueError(f"{relative}: baseline image scalar differs")
            expected_bytes = source_bytes.replace(old_line, new_line, 1)
        if expected_bytes != (target / relative).read_bytes():
            raise ValueError(f"{relative}: migrated article bytes differ")


def verify_media_overlay(
    source: Path,
    target: Path,
    added_media: set[str],
) -> tuple[int, int]:
    expected_additions = {str(row["result"]) for row in EXPECTED_REPAIRS if row["added"]}
    if added_media != expected_additions:
        raise ValueError("images: repair addition set differs")

    source_files = _regular_media_files(source)
    target_files = _regular_media_files(target)
    if target_files != source_files | added_media:
        raise ValueError("images: migrated-plus-repair file set differs")
    for relative in sorted(source_files):
        if sha256(source / relative) != sha256(target / relative):
            raise ValueError(f"{relative}: migrated bytes differ")
    return len(source_files), len(target_files)


def _regular_media_files(root: Path) -> set[str]:
    files: set[str] = set()
    for category in ("posts", "podcast", "books"):
        category_root = root / "images" / category
        for path in category_root.rglob("*"):
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise ValueError(
                    f"{path.relative_to(root).as_posix()}: media symlinks are not allowed"
                )
            if stat.S_ISREG(metadata.st_mode):
                files.add(path.relative_to(root).as_posix())
            elif not stat.S_ISDIR(metadata.st_mode):
                raise ValueError(
                    f"{path.relative_to(root).as_posix()}: media is not a regular file"
                )
    return files


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
