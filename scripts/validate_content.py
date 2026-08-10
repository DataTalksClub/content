from __future__ import annotations

import argparse
import re
import stat
import urllib.parse
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from typing import Any

import yaml

FRONT_MATTER_DELIMITER = re.compile(r"^---[ \t]*$", re.MULTILINE)
HTML_IMAGE_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
HTML_IMAGE_SOURCE = re.compile(
    r"\bsrc\s*=\s*(?:(?P<quote>['\"])(?P<quoted>.*?)\1|(?P<unquoted>[^\s>]+))",
    re.IGNORECASE,
)
MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*(?:<(?P<angle>[^>]+)>|(?P<plain>[^\s)]+))")
MARKDOWN_IMAGE_REFERENCE = re.compile(r"!\[(?P<alt>[^\]]*)\]\[(?P<label>[^\]]*)\]")
MARKDOWN_IMAGE_SHORTCUT = re.compile(r"!\[(?P<label>[^\]]+)\](?![\[(])")
MARKDOWN_REFERENCE_DEFINITION = re.compile(
    r"^[ \t]{0,3}\[(?P<label>[^\]]+)\]:[ \t]*"
    r"(?:<(?P<angle>[^>\r\n]+)>|(?P<plain>\S+))",
    re.MULTILINE,
)
MALFORMED_PERCENT_ESCAPE = re.compile(r"%(?![0-9a-fA-F]{2})")

ALLOWED_MEDIA_EXTENSIONS = frozenset({".gif", ".jpeg", ".jpg", ".png", ".svg"})
UNSAFE_INNER_EXTENSIONS = ALLOWED_MEDIA_EXTENSIONS | frozenset(
    {".bat", ".cmd", ".com", ".exe", ".htm", ".html", ".js", ".php", ".sh"}
)
MEDIA_ROOT_BY_KIND = {
    "article": ("images", "posts"),
    "podcast": ("images", "podcast"),
    "book": ("images", "books"),
}
MAX_MEDIA_BYTES = 10 * 1024 * 1024
MAX_VALIDATION_ERRORS = 100


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
    metadata, _ = load_article_document(path)
    return metadata


def load_article_document(path: Path) -> tuple[dict[str, Any], str]:
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
    body = text[delimiters[1].end() :]
    if not body.strip():
        raise ContentError(f"{path}: article body is empty")
    return value, body


def yaml_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.glob("*.yaml") if path.is_file())


def validate_repository(root: Path) -> dict[str, int]:
    root = root.resolve()
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
    referenced_media: set[Path] = set()

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
            metadata, body = load_article_document(path)
        except ContentError as error:
            errors.append(str(error))
            continue
        if not isinstance(metadata.get("title"), str) or not metadata["title"].strip():
            errors.append(f"{path}: title is required")
        _validate_required_media_reference(
            root,
            path,
            "article",
            "image",
            metadata.get("image"),
            errors,
            referenced_media,
        )
        for body_reference in _article_body_media_references(path, body, errors):
            if _is_external_reference(body_reference):
                continue
            _validate_media_reference(
                root,
                path,
                "article",
                "body image",
                body_reference,
                errors,
                referenced_media,
            )

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
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{path}: description must be a non-empty string")
        _validate_required_media_reference(
            root,
            path,
            "podcast",
            "image",
            metadata.get("image"),
            errors,
            referenced_media,
        )
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
        for field in ("cover", "image"):
            _validate_required_media_reference(
                root,
                path,
                "book",
                field,
                metadata.get(field),
                errors,
                referenced_media,
            )

    if errors:
        root_prefix = f"{root.as_posix()}/"
        safe_errors = [error.replace(root_prefix, "") for error in errors]
        bounded_errors = safe_errors[:MAX_VALIDATION_ERRORS]
        omitted = len(errors) - len(bounded_errors)
        if omitted:
            bounded_errors.append(f"validation stopped after {MAX_VALIDATION_ERRORS} errors")
        raise ContentError("\n".join(bounded_errors))

    media_count = sum(
        1
        for category in MEDIA_ROOT_BY_KIND.values()
        for path in (root.joinpath(*category)).rglob("*")
        if path.is_file() and not path.is_symlink()
    )

    return {
        "articles": len(article_paths),
        "podcasts": len(podcast_paths),
        "transcripts": len(transcript_paths),
        "books": len(book_paths),
        "media": media_count,
        "referenced_media": len(referenced_media),
    }


def _article_body_media_references(
    path: Path,
    body: str,
    errors: list[str],
) -> list[str]:
    references: list[str] = []
    definitions = {
        _normalize_markdown_label(match.group("label")): (
            match.group("angle") or match.group("plain") or ""
        )
        for match in MARKDOWN_REFERENCE_DEFINITION.finditer(body)
    }
    for tag in HTML_IMAGE_TAG.findall(body):
        source = HTML_IMAGE_SOURCE.search(tag)
        if source is None:
            errors.append(f"{path}: HTML image is missing src")
            continue
        references.append(source.group("quoted") or source.group("unquoted") or "")
    for match in MARKDOWN_IMAGE.finditer(body):
        references.append(match.group("angle") or match.group("plain") or "")
    for match in MARKDOWN_IMAGE_REFERENCE.finditer(body):
        label = match.group("label") or match.group("alt")
        target = definitions.get(_normalize_markdown_label(label))
        if target is None:
            errors.append(
                f"{path}: Markdown image reference "
                f"{_safe_reference_display(label)!r} has no definition"
            )
        else:
            references.append(target)
    for match in MARKDOWN_IMAGE_SHORTCUT.finditer(body):
        label = match.group("label")
        target = definitions.get(_normalize_markdown_label(label))
        if target is not None:
            references.append(target)
    return references


def _normalize_markdown_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def _is_external_reference(reference: str) -> bool:
    if reference.startswith("//"):
        return True
    scheme = urllib.parse.urlsplit(reference).scheme.lower()
    return scheme in {"http", "https"}


def _validate_required_media_reference(
    root: Path,
    record_path: Path,
    kind: str,
    field: str,
    value: Any,
    errors: list[str],
    referenced_media: set[Path],
) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{record_path}: {field} is required")
        return
    if _is_external_reference(value):
        errors.append(f"{record_path}: {field} must reference repository media")
        return
    _validate_media_reference(
        root,
        record_path,
        kind,
        field,
        value,
        errors,
        referenced_media,
    )


def _validate_media_reference(
    root: Path,
    record_path: Path,
    kind: str,
    field: str,
    reference: str,
    errors: list[str],
    referenced_media: set[Path],
) -> None:
    display_reference = _safe_reference_display(reference)
    error_prefix = f"{record_path}: {field} {display_reference!r}"
    if not reference or reference != reference.strip():
        errors.append(f"{error_prefix}: media path is empty or padded")
        return
    if any(ord(character) < 32 or ord(character) == 127 for character in reference):
        errors.append(f"{error_prefix}: media path contains a control character")
        return
    if "\\" in reference:
        errors.append(f"{error_prefix}: backslashes are not allowed")
        return
    if "?" in reference or "#" in reference:
        errors.append(f"{error_prefix}: query strings and fragments are not allowed")
        return
    if MALFORMED_PERCENT_ESCAPE.search(reference):
        errors.append(f"{error_prefix}: malformed percent escape")
        return

    decoded = urllib.parse.unquote(reference)
    traversal_probe = decoded
    for _ in range(2):
        traversal_probe = urllib.parse.unquote(traversal_probe)
    if any(ord(character) < 32 or ord(character) == 127 for character in traversal_probe):
        errors.append(f"{error_prefix}: encoded control characters are not allowed")
        return
    if "\\" in traversal_probe or "?" in traversal_probe or "#" in traversal_probe:
        errors.append(f"{error_prefix}: encoded path ambiguity is not allowed")
        return
    if re.match(r"^[a-zA-Z]:", traversal_probe) or traversal_probe.startswith("file:"):
        errors.append(f"{error_prefix}: absolute filesystem paths are not allowed")
        return

    if decoded.startswith("/images/"):
        decoded = decoded[1:]
    elif decoded.startswith("/"):
        errors.append(f"{error_prefix}: absolute filesystem paths are not allowed")
        return

    raw_parts = decoded.split("/")
    probe_parts = traversal_probe.lstrip("/").split("/")
    if (
        not decoded.startswith("images/")
        or any(part in {"", ".", ".."} for part in raw_parts)
        or any(part in {"", ".", ".."} for part in probe_parts)
    ):
        errors.append(f"{error_prefix}: media path is outside the repository image roots")
        return

    expected_root = MEDIA_ROOT_BY_KIND[kind]
    if tuple(raw_parts[:2]) != expected_root:
        expected = "/".join(expected_root)
        errors.append(f"{error_prefix}: {kind} media must be below {expected}")
        return

    filename = raw_parts[-1]
    suffixes = Path(filename).suffixes
    extension = Path(filename).suffix
    if extension != extension.lower() or extension not in ALLOWED_MEDIA_EXTENSIONS:
        errors.append(f"{error_prefix}: media extension is not allowed")
        return
    if any(suffix.lower() in UNSAFE_INNER_EXTENSIONS for suffix in suffixes[:-1]):
        errors.append(f"{error_prefix}: double media or active extension is not allowed")
        return

    candidate = root.joinpath(*raw_parts)
    current = root
    try:
        for part in raw_parts:
            current = current / part
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                errors.append(f"{error_prefix}: symlinks are not allowed")
                return
    except FileNotFoundError:
        errors.append(f"{error_prefix}: referenced media does not exist")
        return
    except OSError:
        errors.append(f"{error_prefix}: referenced media is unreadable")
        return

    if not stat.S_ISREG(metadata.st_mode):
        errors.append(f"{error_prefix}: referenced media is not a regular file")
        return
    if metadata.st_size > MAX_MEDIA_BYTES:
        errors.append(f"{error_prefix}: referenced media exceeds the size limit")
        return
    try:
        media = candidate.read_bytes()
    except OSError:
        errors.append(f"{error_prefix}: referenced media is unreadable")
        return
    signature_error = _media_signature_error(extension, media)
    if signature_error:
        errors.append(f"{error_prefix}: {signature_error}")
        return
    referenced_media.add(Path(*raw_parts))


def _media_signature_error(extension: str, media: bytes) -> str | None:
    if extension in {".jpg", ".jpeg"}:
        if _valid_jpeg(media):
            return None
        return "JPEG signature does not match extension"
    if extension == ".png":
        if _valid_png(media):
            return None
        return "PNG signature does not match extension"
    if extension == ".gif":
        if _valid_gif(media):
            return None
        return "GIF signature does not match extension"
    if extension == ".svg":
        return _svg_safety_error(media)
    return "media extension is not allowed"


def _valid_jpeg(media: bytes) -> bool:
    if len(media) < 13 or not media.startswith(b"\xff\xd8") or not media.endswith(b"\xff\xd9"):
        return False
    index = 2
    while index + 4 <= len(media):
        if media[index] != 0xFF:
            return False
        while index < len(media) and media[index] == 0xFF:
            index += 1
        if index >= len(media):
            return False
        marker = media[index]
        index += 1
        if marker in {0x00, 0xD8, 0xD9}:
            continue
        if marker == 0xDA:
            return False
        if index + 2 > len(media):
            return False
        segment_length = int.from_bytes(media[index : index + 2], "big")
        if segment_length < 2 or index + segment_length > len(media):
            return False
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            return (
                segment_length >= 7
                and int.from_bytes(media[index + 3 : index + 5], "big") > 0
                and int.from_bytes(media[index + 5 : index + 7], "big") > 0
            )
        index += segment_length
    return False


def _valid_png(media: bytes) -> bool:
    return (
        len(media) >= 45
        and media.startswith(b"\x89PNG\r\n\x1a\n")
        and media[8:12] == b"\x00\x00\x00\r"
        and media[12:16] == b"IHDR"
        and int.from_bytes(media[16:20], "big") > 0
        and int.from_bytes(media[20:24], "big") > 0
        and media[-12:] == b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _valid_gif(media: bytes) -> bool:
    return (
        len(media) >= 14
        and media.startswith((b"GIF87a", b"GIF89a"))
        and int.from_bytes(media[6:8], "little") > 0
        and int.from_bytes(media[8:10], "little") > 0
        and media.endswith(b";")
    )


def _svg_safety_error(media: bytes) -> str | None:
    try:
        text = media.decode("utf-8")
    except UnicodeDecodeError:
        return "SVG must be UTF-8"
    lowered = text.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        return "unsafe SVG declaration"
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        return "invalid SVG content"
    if root.tag.rsplit("}", 1)[-1].lower() != "svg":
        return "SVG root element is invalid"

    unsafe_elements = {"embed", "foreignobject", "iframe", "object", "script"}
    for element in root.iter():
        element_name = element.tag.rsplit("}", 1)[-1].lower()
        if element_name in unsafe_elements:
            return "unsafe SVG element"
        if element_name == "style" and _unsafe_css(element.text or ""):
            return "unsafe SVG style"
        for raw_name, raw_value in element.attrib.items():
            name = raw_name.rsplit("}", 1)[-1].lower()
            value = raw_value.strip().lower()
            if name.startswith("on"):
                return "unsafe SVG event handler"
            if name in {"href", "src"} and value and not value.startswith("#"):
                return "external SVG reference"
            if "javascript:" in value or "@import" in value:
                return "unsafe SVG attribute"
            if _unsafe_css(value):
                return "external SVG reference"
    return None


def _unsafe_css(value: str) -> bool:
    lowered = value.lower()
    if "@import" in lowered or "javascript:" in lowered:
        return True
    return any(
        not url.strip(" '\"").startswith("#") for url in re.findall(r"url\((.*?)\)", lowered)
    )


def _safe_reference_display(reference: str) -> str:
    rendered = "".join(character if 32 <= ord(character) < 127 else "?" for character in reference)
    return rendered[:240]


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
