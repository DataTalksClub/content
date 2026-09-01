from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Any

ARTICLE_DATE_FIELD = "datepublished"
BOOK_DATE_FIELD = "start"
ARTICLE_FILENAME_RE = re.compile(
    r"^(?P<year>[0-9]{2})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})-(?P<slug>[a-z0-9][a-z0-9.-]*)\.md$"
)
BOOK_FILENAME_RE = re.compile(
    r"^(?P<year>[0-9]{2})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})-(?P<slug>[a-z0-9][a-z0-9.-]*)\.yaml$"
)
DATED_ARTICLE_SOURCE_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-(?P<slug>[a-z0-9][a-z0-9.-]*)\.md$"
)
DATED_BOOK_SLUG_RE = re.compile(r"^[0-9]{8}-(?P<slug>[a-z0-9][a-z0-9.-]*)$")


class ContentLayoutError(ValueError):
    """A content record cannot be placed in the dated source layout."""


def parse_metadata_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def metadata_date(metadata: dict[str, Any], field: str) -> date | None:
    return parse_metadata_date(metadata.get(field))


def article_slug(source_path: Path) -> str:
    match = DATED_ARTICLE_SOURCE_RE.fullmatch(source_path.name)
    if match is not None:
        return match.group("slug")
    match = ARTICLE_FILENAME_RE.fullmatch(source_path.name)
    return match.group("slug") if match is not None else source_path.stem


def book_slug(metadata: dict[str, Any], source_path: Path) -> str:
    value = metadata.get("slug")
    if not isinstance(value, str) or not value or Path(value).name != value:
        raise ContentLayoutError(f"{source_path}: slug is required for the dated book layout")
    return value


def book_filename_slug(slug: str) -> str:
    match = DATED_BOOK_SLUG_RE.fullmatch(slug)
    return match.group("slug") if match is not None else slug


def article_target_path(source_path: Path, metadata: dict[str, Any]) -> Path:
    published = metadata_date(metadata, ARTICLE_DATE_FIELD)
    if published is None:
        raise ContentLayoutError(
            f"{source_path}: {ARTICLE_DATE_FIELD} is missing or not a usable YYYY-MM-DD date"
        )
    return Path(str(published.year)) / f"{published:%y-%m-%d}-{article_slug(source_path)}.md"


def book_target_path(
    source_path: Path,
    metadata: dict[str, Any],
    *,
    slug: str | None = None,
) -> Path:
    started = metadata_date(metadata, BOOK_DATE_FIELD)
    if started is None:
        raise ContentLayoutError(
            f"{source_path}: {BOOK_DATE_FIELD} is missing or not a usable YYYY-MM-DD date"
        )
    canonical_slug = slug if slug is not None else book_slug(metadata, source_path)
    if not canonical_slug or Path(canonical_slug).name != canonical_slug:
        raise ContentLayoutError(f"{source_path}: slug is not a filename-safe value")
    return Path(str(started.year)) / f"{started:%y-%m-%d}-{book_filename_slug(canonical_slug)}.yaml"


def discover_article_paths(articles_dir: Path) -> list[Path]:
    return _discover_paths(articles_dir, ".md")


def discover_book_paths(books_dir: Path) -> list[Path]:
    return _discover_paths(books_dir, ".yaml")


def _discover_paths(directory: Path, suffix: str) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.rglob(f"*{suffix}") if path.is_file())


def expected_dated_path(
    path: Path,
    directory: Path,
    metadata: dict[str, Any],
    *,
    kind: str,
) -> Path | None:
    try:
        relative = path.relative_to(directory)
    except ValueError:
        return None
    if kind == "article":
        expected_date = metadata_date(metadata, ARTICLE_DATE_FIELD)
        pattern = ARTICLE_FILENAME_RE
    elif kind == "book":
        expected_date = metadata_date(metadata, BOOK_DATE_FIELD)
        pattern = BOOK_FILENAME_RE
    else:
        raise ValueError(f"unsupported content kind: {kind}")
    if expected_date is None or len(relative.parts) != 2:
        return None
    match = pattern.fullmatch(relative.name)
    if match is None:
        return None
    try:
        expected = (
            article_target_path(path, metadata)
            if kind == "article"
            else book_target_path(path, metadata)
        )
    except ContentLayoutError:
        return None
    if relative != expected:
        return None
    return relative


def unique_target_paths(
    records: Iterable[tuple[Path, dict[str, Any]]],
    *,
    kind: str,
) -> dict[Path, Path]:
    targets: dict[Path, Path] = {}
    for source_path, metadata in records:
        target = (
            article_target_path(source_path, metadata)
            if kind == "article"
            else book_target_path(source_path, metadata, slug=source_path.stem)
        )
        previous = targets.setdefault(target, source_path)
        if previous != source_path:
            raise ContentLayoutError(f"{source_path}: dated path {target} collides with {previous}")
    return targets
