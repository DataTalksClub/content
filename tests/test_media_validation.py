from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.validate_content import (
    MAX_MEDIA_BYTES,
    ContentError,
    _media_signature_error,
    validate_repository,
)

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDAT\x08\xd7c\xf8\xcf"
    b"\xc0\xf0\x1f\x00\x05\x00\x01\xff\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _build_repository(tmp_path: Path, *, article_image: str | None = None) -> Path:
    for relative in (
        "articles",
        "podcasts/transcripts",
        "books",
        "images/posts/article",
        "images/podcast",
        "images/books/book",
    ):
        (tmp_path / relative).mkdir(parents=True, exist_ok=True)
    _write_png(tmp_path / "images/posts/article/cover.png")
    _write_png(tmp_path / "images/podcast/podcast.png")
    _write_png(tmp_path / "images/books/book/cover.png")
    _write_png(tmp_path / "images/books/book/preview.png")
    image = article_image or "images/posts/article/cover.png"
    (tmp_path / "articles/article.md").write_text(
        f"---\ntitle: Article\nimage: {image}\n---\n\nArticle body.\n",
        encoding="utf-8",
    )
    (tmp_path / "podcasts/podcast.yaml").write_text(
        "\n".join(
            (
                "slug: podcast",
                "legacy_path: /podcast/podcast.html",
                "title: Podcast",
                "season: 1",
                "episode: 1",
                "guests: []",
                "image: images/podcast/podcast.png",
                "",
            )
        ),
        encoding="utf-8",
    )
    (tmp_path / "books/book.yaml").write_text(
        "\n".join(
            (
                "slug: book",
                "legacy_path: /books/book.html",
                "title: Book",
                "summary: Summary",
                "cover: images/books/book/cover.png",
                "image: images/books/book/preview.png",
                "",
            )
        ),
        encoding="utf-8",
    )
    return tmp_path


def _write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PNG)


def _set_article_body(root: Path, body: str) -> None:
    (root / "articles/article.md").write_text(
        f"---\ntitle: Article\nimage: images/posts/article/cover.png\n---\n\n{body}\n",
        encoding="utf-8",
    )


def test_validates_inline_html_and_reference_style_markdown_images(tmp_path: Path) -> None:
    root = _build_repository(tmp_path)
    for name in ("inline", "html", "reference", "shortcut"):
        _write_png(root / f"images/posts/article/{name}.png")
    _set_article_body(
        root,
        "\n".join(
            (
                "![inline](images/posts/article/inline.png)",
                '<img src="/images/posts/article/html.png" alt="HTML">',
                "![reference][cover]",
                "![shortcut]",
                "[cover]: images/posts/article/reference.png",
                "[shortcut]: <images/posts/article/shortcut.png>",
                "![external](https://example.com/image.png)",
                '<img src="//example.com/image.png">',
                "[ordinary link](images/posts/article/missing.png)",
            )
        ),
    )

    counts = validate_repository(root)

    assert counts["referenced_media"] == 8


def test_reference_style_markdown_missing_media_fails_closed(tmp_path: Path) -> None:
    root = _build_repository(tmp_path)
    _set_article_body(
        root,
        "![cover][hero]\n\n[hero]: images/posts/article/missing.png",
    )

    with pytest.raises(ContentError, match="referenced media does not exist"):
        validate_repository(root)


def test_undefined_reference_style_markdown_image_fails_closed(tmp_path: Path) -> None:
    root = _build_repository(tmp_path)
    _set_article_body(root, "![cover][undefined]")

    with pytest.raises(
        ContentError, match="Markdown image reference 'undefined' has no definition"
    ):
        validate_repository(root)


@pytest.mark.parametrize(
    ("reference", "message"),
    (
        ("' ../cover.png'", "empty or padded"),
        ("../cover.png", "outside the repository image roots"),
        ("images/posts/%2e%2e/cover.png", "outside the repository image roots"),
        ("images/posts/%252e%252e/cover.png", "outside the repository image roots"),
        (r"images\posts\cover.png", "backslashes are not allowed"),
        ("/etc/passwd", "absolute filesystem paths are not allowed"),
        ("C:/images/posts/cover.png", "absolute filesystem paths are not allowed"),
        ("images/posts/article/cover.png?raw=1", "query strings and fragments"),
        ("images/posts/article/cover.png#fragment", "query strings and fragments"),
        ("images/podcast/podcast.png", "article media must be below images/posts"),
        ("images/posts/article/cover.PNG", "media extension is not allowed"),
        ("images/posts/article/cover.jpg.png", "double media or active extension"),
        ("images/posts/article/cover.txt", "media extension is not allowed"),
        ("images/posts/article/cover%zz.png", "malformed percent escape"),
        ("images/posts/article/cover%00.png", "encoded control characters"),
    ),
)
def test_rejects_unsafe_article_metadata_paths(
    tmp_path: Path,
    reference: str,
    message: str,
) -> None:
    root = _build_repository(tmp_path, article_image=reference)

    with pytest.raises(ContentError, match=message):
        validate_repository(root)


def test_rejects_wrong_magic_bytes(tmp_path: Path) -> None:
    root = _build_repository(tmp_path)
    (root / "images/posts/article/cover.png").write_bytes(b"not a png")

    with pytest.raises(ContentError, match="PNG signature does not match extension"):
        validate_repository(root)


def test_rejects_literal_control_character_without_leaking_it(tmp_path: Path) -> None:
    root = _build_repository(tmp_path)
    _set_article_body(root, "![unsafe](images/posts/article/\x01cover.png)")

    with pytest.raises(ContentError, match="control character") as captured:
        validate_repository(root)

    assert "\x01" not in str(captured.value)


@pytest.mark.parametrize(
    ("extension", "media"),
    (
        (".jpg", b"\xff\xd8\xff"),
        (".png", b"\x89PNG\r\n\x1a\n"),
        (".gif", b"GIF89a"),
    ),
)
def test_bare_image_signature_prefix_is_not_a_valid_image(
    extension: str,
    media: bytes,
) -> None:
    assert _media_signature_error(extension, media) is not None


@pytest.mark.parametrize(
    "svg",
    (
        '<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="https://evil.test/a"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><style>@import "https://evil.test/a";</style></svg>',
        (
            '<svg xmlns="http://www.w3.org/2000/svg"><style>'
            "path { fill: url(https://evil.test/a); }</style></svg>"
        ),
        '<svg xmlns="http://www.w3.org/2000/svg"><path onclick="alert(1)"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><path style="fill:url(https://evil.test/a)"/></svg>',
    ),
)
def test_rejects_unsafe_or_external_svg(tmp_path: Path, svg: str) -> None:
    root = _build_repository(tmp_path, article_image="images/posts/article/cover.svg")
    (root / "images/posts/article/cover.svg").write_text(svg, encoding="utf-8")

    with pytest.raises(ContentError, match="SVG"):
        validate_repository(root)


def test_allows_internal_svg_fragment_reference(tmp_path: Path) -> None:
    root = _build_repository(tmp_path, article_image="images/posts/article/cover.svg")
    (root / "images/posts/article/cover.svg").write_text(
        """<svg xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="gradient"/></defs>
  <path style="fill:url(#gradient)"/>
</svg>
""",
        encoding="utf-8",
    )

    validate_repository(root)


@pytest.mark.parametrize("kind", ("symlink", "directory", "fifo"))
def test_rejects_non_regular_media(tmp_path: Path, kind: str) -> None:
    root = _build_repository(tmp_path)
    target = root / "images/posts/article/cover.png"
    target.unlink()
    if kind == "symlink":
        target.symlink_to(root / "images/podcast/podcast.png")
    elif kind == "directory":
        target.mkdir()
    else:
        os.mkfifo(target)

    with pytest.raises(ContentError, match="symlinks|not a regular file"):
        validate_repository(root)


def test_rejects_oversized_media_without_reading_it(tmp_path: Path) -> None:
    root = _build_repository(tmp_path)
    target = root / "images/posts/article/cover.png"
    with target.open("wb") as stream:
        stream.seek(MAX_MEDIA_BYTES)
        stream.write(b"x")

    with pytest.raises(ContentError, match="exceeds the size limit"):
        validate_repository(root)


def test_errors_are_bounded_relative_and_do_not_include_article_body(tmp_path: Path) -> None:
    root = _build_repository(tmp_path)
    secret_marker = "DO-NOT-LEAK-ARTICLE-BODY"
    body = "\n".join(
        f"![missing {index}](images/posts/article/missing-{index}.png)" for index in range(110)
    )
    _set_article_body(root, f"{secret_marker}\n{body}")

    with pytest.raises(ContentError) as captured:
        validate_repository(root)

    error = str(captured.value)
    assert secret_marker not in error
    assert tmp_path.as_posix() not in error
    assert "validation stopped after 100 errors" in error
