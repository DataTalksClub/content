from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

FRONT_MATTER_DELIMITER = re.compile(r"^---[ \t]*$", re.MULTILINE)


class ContentError(ValueError):
    """A safe, path-specific content validation error."""


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ContentError(f"{path}: invalid YAML") from error
    if not isinstance(value, dict):
        raise ContentError(f"{path}: expected a YAML mapping")
    return value


def load_article_front_matter(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ContentError(f"{path}: unreadable article") from error
    delimiters = list(FRONT_MATTER_DELIMITER.finditer(text))
    if len(delimiters) < 2 or text[: delimiters[0].start()].strip():
        raise ContentError(f"{path}: expected leading YAML front matter")
    try:
        value = yaml.safe_load(text[delimiters[0].end() : delimiters[1].start()])
    except yaml.YAMLError as error:
        raise ContentError(f"{path}: invalid YAML front matter") from error
    if not isinstance(value, dict):
        raise ContentError(f"{path}: front matter must be a mapping")
    if not text[delimiters[1].end() :].strip():
        raise ContentError(f"{path}: article body is empty")
    return value


def yaml_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.glob("*.yaml") if path.is_file())


def validate_repository(root: Path) -> dict[str, int]:
    errors: list[str] = []
    articles_dir = root / "articles"
    podcasts_dir = root / "podcasts"
    transcripts_dir = podcasts_dir / "transcripts"
    books_dir = root / "books"

    for directory in (articles_dir, podcasts_dir, transcripts_dir, books_dir):
        if not directory.is_dir():
            errors.append(f"{directory}: required directory is missing")

    article_paths = sorted(articles_dir.glob("*.md")) if articles_dir.is_dir() else []
    podcast_paths = yaml_files(podcasts_dir) if podcasts_dir.is_dir() else []
    transcript_paths = yaml_files(transcripts_dir) if transcripts_dir.is_dir() else []
    book_paths = yaml_files(books_dir) if books_dir.is_dir() else []

    unsupported = []
    if articles_dir.is_dir():
        unsupported.extend(articles_dir.glob("*.yaml"))
    if podcasts_dir.is_dir():
        unsupported.extend(podcasts_dir.glob("*.md"))
    if books_dir.is_dir():
        unsupported.extend(books_dir.glob("*.md"))
    errors.extend(f"{path}: unsupported content file type" for path in sorted(unsupported))

    for path in article_paths:
        try:
            metadata = load_article_front_matter(path)
        except ContentError as error:
            errors.append(str(error))
            continue
        if not isinstance(metadata.get("title"), str) or not metadata["title"].strip():
            errors.append(f"{path}: title is required")

    slugs: dict[str, Path] = {}
    legacy_paths: dict[str, Path] = {}
    expected_transcripts: dict[Path, str] = {}

    for path in podcast_paths:
        try:
            metadata = load_yaml_mapping(path)
        except ContentError as error:
            errors.append(str(error))
            continue
        _validate_identity(path, metadata, slugs, legacy_paths, errors)
        for key in ("title", "season", "episode", "guests"):
            if key not in metadata:
                errors.append(f"{path}: {key} is required")
        transcript = metadata.get("transcript")
        if isinstance(transcript, list):
            errors.append(f"{path}: transcript must be stored in a separate YAML file")
        elif transcript is not None:
            if not isinstance(transcript, str):
                errors.append(f"{path}: transcript reference must be a string")
            else:
                target = podcasts_dir / transcript
                try:
                    target.relative_to(transcripts_dir)
                except ValueError:
                    errors.append(f"{path}: transcript must be below podcasts/transcripts")
                else:
                    expected_transcripts[target] = str(metadata.get("slug", ""))
                    if not target.is_file():
                        errors.append(f"{path}: referenced transcript does not exist")

    actual_transcripts = set(transcript_paths)
    for path in transcript_paths:
        try:
            transcript = load_yaml_mapping(path)
        except ContentError as error:
            errors.append(str(error))
            continue
        podcast = transcript.get("podcast")
        segments = transcript.get("segments")
        if podcast != expected_transcripts.get(path):
            errors.append(f"{path}: podcast does not match its episode reference")
        if not isinstance(segments, list):
            errors.append(f"{path}: segments must be a list")
        elif any(not isinstance(segment, dict) for segment in segments):
            errors.append(f"{path}: every transcript segment must be a mapping")

    for orphan in sorted(actual_transcripts - set(expected_transcripts)):
        errors.append(f"{orphan}: orphaned transcript")

    for path in book_paths:
        try:
            metadata = load_yaml_mapping(path)
        except ContentError as error:
            errors.append(str(error))
            continue
        _validate_identity(path, metadata, slugs, legacy_paths, errors)
        if not isinstance(metadata.get("title"), str) or not metadata["title"].strip():
            errors.append(f"{path}: title is required")
        if not isinstance(metadata.get("summary"), str) or not metadata["summary"].strip():
            errors.append(f"{path}: summary is required")

    if errors:
        raise ContentError("\n".join(errors))

    return {
        "articles": len(article_paths),
        "podcasts": len(podcast_paths),
        "transcripts": len(transcript_paths),
        "books": len(book_paths),
    }


def _validate_identity(
    path: Path,
    metadata: dict[str, Any],
    slugs: dict[str, Path],
    legacy_paths: dict[str, Path],
    errors: list[str],
) -> None:
    for key, registry in (("slug", slugs), ("legacy_path", legacy_paths)):
        value = metadata.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{path}: {key} is required")
            continue
        previous = registry.setdefault(value, path)
        if previous != path:
            errors.append(f"{path}: duplicate {key} also used by {previous}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate DataTalks.Club content")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        counts = validate_repository(args.root.resolve())
    except ContentError as error:
        print(f"STOP: {error}")
        return 1
    rendered = ", ".join(f"{name}={count}" for name, count in counts.items())
    print(f"PASS: {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
