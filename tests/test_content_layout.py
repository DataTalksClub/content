from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from scripts.content_layout import (
    ContentLayoutError,
    article_target_path,
    book_target_path,
    discover_article_paths,
    discover_book_paths,
    expected_dated_path,
    parse_metadata_date,
)
from scripts.validate_content import (
    ContentError,
    load_article_front_matter,
    load_yaml_mapping,
    validate_repository,
)

ROOT = Path(__file__).resolve().parents[1]


def test_checked_records_use_metadata_derived_paths() -> None:
    article_paths = discover_article_paths(ROOT / "articles")
    book_paths = discover_book_paths(ROOT / "books")

    assert len(article_paths) == 55
    assert len(book_paths) == 98
    assert all(len(path.relative_to(ROOT / "articles").parts) == 2 for path in article_paths)
    assert all(len(path.relative_to(ROOT / "books").parts) == 2 for path in book_paths)

    for path in article_paths:
        metadata = load_article_front_matter(path)
        assert expected_dated_path(path, ROOT / "articles", metadata, kind="article") is not None

    for path in book_paths:
        metadata = load_yaml_mapping(path)
        assert expected_dated_path(path, ROOT / "books", metadata, kind="book") is not None


def test_book_path_uses_start_date_when_filename_prefix_differs() -> None:
    path = ROOT / "books/2022/22-10-24-comet-for-data-science.yaml"
    metadata = load_yaml_mapping(path)

    assert metadata["slug"] == "20221107-comet-for-data-science"
    assert book_target_path(path, metadata) == Path("2022/22-10-24-comet-for-data-science.yaml")


def test_article_path_remains_stable_after_move() -> None:
    path = ROOT / "articles/2024/24-04-11-guide-to-free-online-courses-at-datatalks-club.md"
    metadata = load_article_front_matter(path)

    assert article_target_path(path, metadata) == Path(
        "2024/24-04-11-guide-to-free-online-courses-at-datatalks-club.md"
    )


@pytest.mark.parametrize(
    ("relative", "document"),
    (
        (
            "articles/2024-01-02-example.md",
            "---\ntitle: Article\ndatepublished: 2024-01-02\n---\nBody\n",
        ),
        (
            "books/2024-01-02-example.yaml",
            "slug: 20240102-example\nlegacy_path: /books/example.html\n"
            "title: Book\nstart: 2024-01-02\nsummary: Summary\n",
        ),
    ),
)
def test_validator_rejects_flat_dated_records(
    tmp_path: Path,
    relative: str,
    document: str,
) -> None:
    for directory in ("articles", "podcasts", "books"):
        (tmp_path / directory).mkdir()
    (tmp_path / relative).write_text(document, encoding="utf-8")

    with pytest.raises(ContentError, match="path does not match the dated"):
        validate_repository(tmp_path)


def test_date_parser_accepts_yaml_date_values_and_rejects_ambiguous_values() -> None:
    assert parse_metadata_date(date(2024, 1, 2)) == date(2024, 1, 2)
    assert parse_metadata_date(datetime(2024, 1, 2, 12, 30)) == date(2024, 1, 2)
    assert parse_metadata_date("2024-01-02") == date(2024, 1, 2)
    assert parse_metadata_date("2024-1-2") is None
    assert parse_metadata_date("not-a-date") is None


def test_missing_dates_never_fall_back_to_the_filename() -> None:
    with_error = {"title": "Article"}
    with_error_book = {"slug": "20240102-book", "title": "Book"}

    try:
        article_target_path(Path("2024-01-02-article.md"), with_error)
    except ContentLayoutError as error:
        assert "datepublished" in str(error)
    else:
        raise AssertionError("an undated article must not receive an invented date")

    try:
        book_target_path(Path("20240102-book.yaml"), with_error_book)
    except ContentLayoutError as error:
        assert "start" in str(error)
    else:
        raise AssertionError("an undated book must not receive an invented date")
