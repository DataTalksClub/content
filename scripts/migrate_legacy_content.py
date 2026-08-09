from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

FRONT_MATTER_DELIMITER = re.compile(r"^---[ \t]*$", re.MULTILINE)
MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def read_legacy_document(path: Path) -> tuple[dict[str, Any], str, str]:
    text = path.read_text(encoding="utf-8")
    delimiters = list(FRONT_MATTER_DELIMITER.finditer(text))
    if len(delimiters) < 2:
        raise ValueError(f"{path}: expected leading YAML front matter")
    legacy_prefix = text[: delimiters[0].start()].strip()
    if legacy_prefix not in {"", "_"}:
        raise ValueError(f"{path}: unexpected content before YAML front matter")
    metadata = yaml.safe_load(text[delimiters[0].end() : delimiters[1].start()])
    if not isinstance(metadata, dict):
        raise ValueError(f"{path}: front matter must be a mapping")
    body = text[delimiters[1].end() :].strip()
    return metadata, body, legacy_prefix


def write_yaml(path: Path, value: Any) -> None:
    path.write_text(
        yaml.safe_dump(
            value,
            allow_unicode=True,
            sort_keys=False,
            width=100,
        ),
        encoding="utf-8",
    )


def slug_for(path: Path) -> str:
    return path.name.removesuffix(".md")


def resources_from_body(body: str) -> list[dict[str, str]] | None:
    if not body.lower().startswith("links:"):
        return None
    links = MARKDOWN_LINK.findall(body)
    if not links:
        return None
    remainder = MARKDOWN_LINK.sub("", body)
    remainder = re.sub(r"\{:\s*target=[^}]+\}", "", remainder)
    remainder = re.sub(r"(?im)^\s*links:\s*$", "", remainder)
    remainder = re.sub(r"[\s*\-]+", "", remainder)
    if remainder:
        return None
    return [{"title": title.strip(), "url": url} for title, url in links]


def ensure_empty_targets(target: Path) -> None:
    for relative in ("articles", "podcasts", "books", "images"):
        candidate = target / relative
        if candidate.exists() and any(candidate.iterdir()):
            raise ValueError(f"{candidate}: target must be empty before migration")


def migrate(source: Path, target: Path, migration_date: str) -> dict[str, Any]:
    ensure_empty_targets(target)
    articles_dir = target / "articles"
    podcasts_dir = target / "podcasts"
    transcripts_dir = podcasts_dir / "transcripts"
    books_dir = target / "books"
    for directory in (articles_dir, podcasts_dir, transcripts_dir, books_dir):
        directory.mkdir(parents=True, exist_ok=True)

    article_sources = sorted((source / "_posts").glob("*.md"))
    for path in article_sources:
        shutil.copy2(path, articles_dir / path.name)

    podcast_sources = sorted(
        path for path in (source / "_podcast").glob("*.md") if path.name != "_template.md"
    )
    transcript_count = 0
    for path in podcast_sources:
        metadata, body, legacy_prefix = read_legacy_document(path)
        slug = slug_for(path)
        transcript = metadata.pop("transcript", None)
        converted: dict[str, Any] = {
            "slug": slug,
            "legacy_path": f"/podcast/{slug}.html",
            **metadata,
        }
        if legacy_prefix:
            converted["legacy_prefix"] = legacy_prefix
        if transcript is not None:
            if not isinstance(transcript, list):
                raise ValueError(f"{path}: transcript must be a list")
            transcript_name = f"{slug}.yaml"
            converted["transcript"] = f"transcripts/{transcript_name}"
            write_yaml(
                transcripts_dir / transcript_name,
                {"podcast": slug, "segments": transcript},
            )
            transcript_count += 1
        if body:
            resources = resources_from_body(body)
            if resources is not None:
                converted["resources"] = resources
            else:
                converted["notes"] = body
        write_yaml(podcasts_dir / f"{slug}.yaml", converted)

    book_sources = sorted(
        path for path in (source / "_books").glob("*.md") if path.name != "_template.md"
    )
    for path in book_sources:
        metadata, body, legacy_prefix = read_legacy_document(path)
        if legacy_prefix:
            raise ValueError(f"{path}: books may not have content before front matter")
        slug = slug_for(path)
        converted = {
            "slug": slug,
            "legacy_path": f"/books/{slug}.html",
            **metadata,
            "summary": body,
        }
        write_yaml(books_dir / f"{slug}.yaml", converted)

    for category in ("posts", "podcast", "books"):
        source_images = source / "images" / category
        shutil.copytree(source_images, target / "images" / category)

    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    provenance = {
        "schema_version": 1,
        "migration_date": migration_date,
        "source": {
            "repository": "https://github.com/DataTalksClub/datatalksclub.github.io",
            "revision": revision,
        },
        "counts": {
            "articles": len(article_sources),
            "podcasts": len(podcast_sources),
            "podcast_transcripts": transcript_count,
            "books": len(book_sources),
        },
        "rules": {
            "articles": "copied byte-for-byte with YAML front matter and Markdown body",
            "podcasts": "converted to YAML; transcript arrays moved to separate YAML files",
            "books": "converted to YAML; Markdown body moved to the summary field",
            "templates": "legacy _template.md files excluded",
            "images": "copied byte-for-byte at legacy relative paths",
        },
    }
    write_yaml(target / "migration.yaml", provenance)
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate the legacy DataTalks.Club content")
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--target",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--migration-date", required=True)
    args = parser.parse_args()
    provenance = migrate(args.source.resolve(), args.target.resolve(), args.migration_date)
    counts = provenance["counts"]
    rendered = ", ".join(f"{name}={count}" for name, count in counts.items())
    print(f"Migrated {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
