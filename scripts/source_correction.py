"""Validate the narrowly scoped post-migration source correction overlay.

The legacy migration remains immutable.  This module describes and applies the
only source-owned corrections that are allowed after that migration: five
complete link-destination replacements in one article, one podcast ``image``
scalar correction, and one lossless media rename.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

MANIFEST_RELATIVE_PATH = Path("editorial-overlays/2026-09-01-source-corrections.yaml")
EXPECTED_MANIFEST_SHA256 = "8f53623a0858ee34e15bce8b333b690a7422c47413e984d773e3f18fe62b44f0"
ISSUE_URL = "https://github.com/DataTalksClub/website/issues/253"
CREATED = "2026-09-01"
BASELINE_CONTENT_COMMIT = "b02354255d2aedb686e3176074890868a39d928e"
BASELINE_CONTENT_TREE = "9f393ba6b97f23963c065b9c8e34f6238c920186"
SOURCE_REPOSITORY = "https://github.com/DataTalksClub/datatalksclub.github.io"
SOURCE_COMMIT = "ee43d3fa0929faf691178d79f19528e6f15a83e5"
MIGRATION_MANIFEST_RELATIVE_PATH = "migration.yaml"
MIGRATION_MANIFEST_SHA256 = "dd78a343a5f387a74afa914fc6c7e19790e202aa5d6fa9aba08bfda5995c5f86"

ARTICLE_PATH = "articles/2025-09-23-ai-dev-tools-zoomcamp.md"
ARTICLE_LEGACY_PATH = "_posts/2025-09-23-ai-dev-tools-zoomcamp.md"
ARTICLE_LEGACY_BLOB = "605cea29368c8647d6471f5599e57d5460dae0fa"
ARTICLE_LEGACY_SHA256 = "afbb979e31ede1922f093a6d14472dd08cf0fe83f48132adb778dbaf21e31e7a"
ARTICLE_TARGET_BLOB = "cfbb898b0d40b1d1d1b74761f8cdfa783659f53f"
ARTICLE_TARGET_SHA256 = "0515ed5b52ae8e1f21b9caaf2b0a716f0df58072568558e86700547b40dbbaf4"

PODCAST_PATH = "podcasts/s24e06-how-to-build-ai-that-actually-ships-in-production.yaml"
PODCAST_LEGACY_PATH = "_podcast/s24e06-how-to-build-ai-that-actually-ships-in-production.md"
PODCAST_BASELINE_BLOB = "63445f9de4506f76f8d9bf537bd734ce9566f98a"
PODCAST_BASELINE_SHA256 = "47c8d1fcb41f1dfe855cecb477fbada147420fea20fccac9c676cf854f915234"
PODCAST_TARGET_BLOB = "3dee1e63aa3be528dfd3b0792acdb96eefecb496"
PODCAST_TARGET_SHA256 = "62554e94b5d8ab04ab7f7b060ffec0fa6ff7c61e53a2b929f7f6db1b3df25c90"
PODCAST_FIELD = "image"
PODCAST_OLD_VALUE = "images/podcast/s24e07-how-to-build-ai-that-actually-ships-in-production.jpg"
PODCAST_NEW_VALUE = "images/podcast/s24e06-how-to-build-ai-that-actually-ships-in-production.jpg"

MEDIA_OLD_PATH = "images/podcast/s24e07-how-to-build-ai-that-actually-ships-in-production.jpg"
MEDIA_NEW_PATH = "images/podcast/s24e06-how-to-build-ai-that-actually-ships-in-production.jpg"
MEDIA_BLOB = "ed5345e6c4b6f84a1ebf46e6aeb61cef532fa467"
MEDIA_SHA256 = "f930cd185a60a6478695db674b38e90689aae68628df2aad554d8a5c2386c374"
MEDIA_BYTES = 38743

EXPECTED_REPLACEMENTS: tuple[dict[str, Any], ...] = (
    {
        "match": "markdown_destination",
        "old": "https://alexeyondata.substack.com/p/ai-native-development-specifications",
        "new": "https://aishippingblog.com/p/ai-native-development-specifications",
        "occurrences": 2,
        "line_numbers": (137, 194),
    },
    {
        "match": "html_href",
        "old": "https://alexeyondata.substack.com/p/ai-native-development-specifications",
        "new": "https://aishippingblog.com/p/ai-native-development-specifications",
        "occurrences": 1,
        "line_numbers": (225,),
    },
    {
        "match": "markdown_destination",
        "old": "https://alexeyondata.substack.com/",
        "new": "https://aishippingblog.com/",
        "occurrences": 1,
        "line_numbers": (192,),
    },
    {
        "match": "html_href",
        "old": "https://alexeyondata.substack.com/",
        "new": "https://aishippingblog.com/",
        "occurrences": 1,
        "line_numbers": (200,),
    },
)
EXPECTED_CHANGED_PATHS = (
    ("M", ".github/workflows/validate.yml"),
    ("M", "Makefile"),
    ("M", "README.md"),
    ("M", "editorial-overlays/2026-08-10-podcast-descriptions.yaml"),
    ("A", "editorial-overlays/2026-09-01-source-corrections.yaml"),
    (
        "R100",
        MEDIA_OLD_PATH,
        MEDIA_NEW_PATH,
    ),
    ("M", PODCAST_PATH),
    ("M", "scripts/editorial_overlay.py"),
    ("A", "scripts/source_correction.py"),
    ("M", "scripts/verify_migration.py"),
    ("A", "tests/test_source_correction.py"),
)

TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "kind",
        "issue",
        "created",
        "baseline",
        "source",
        "replacement_count",
        "changed_paths",
        "articles",
        "podcasts",
        "media_renames",
    }
)
BASELINE_KEYS = frozenset(
    {"content_commit", "content_tree", "migration_manifest", "migration_manifest_sha256"}
)
SOURCE_KEYS = frozenset({"repository", "commit"})
ARTICLE_KEYS = frozenset(
    {
        "path",
        "legacy_path",
        "legacy_blob",
        "legacy_sha256",
        "target_blob",
        "target_sha256",
        "replacement_count",
        "replacements",
    }
)
REPLACEMENT_KEYS = frozenset({"match", "old", "new", "occurrences", "line_numbers"})
PODCAST_KEYS = frozenset(
    {
        "path",
        "legacy_path",
        "baseline_blob",
        "baseline_sha256",
        "target_blob",
        "target_sha256",
        "field",
        "old",
        "new",
        "occurrences",
    }
)
MEDIA_KEYS = frozenset({"old_path", "new_path", "blob", "sha256", "bytes"})
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
MATCH_KINDS = frozenset({"markdown_destination", "html_href"})
MARKDOWN_DESTINATION_RE = re.compile(r"\]\((?P<url>[^)\r\n]*)\)")
HTML_HREF_RE = re.compile(r"(?i)\bhref\s*=\s*(?P<quote>[\"'])(?P<url>[^\"'\r\n]*)(?P=quote)")


class SourceCorrectionError(ValueError):
    """A bounded, content-free source correction contract failure."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha(data: bytes) -> str:
    """Return the SHA-1 Git uses for a regular blob with ``data``."""

    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - Git's fixed blob hash


def load_source_correction(path: Path) -> dict[str, Any]:
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise SourceCorrectionError("source correction manifest is not a regular file")
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except SourceCorrectionError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise SourceCorrectionError(
            "source correction manifest is unreadable or invalid YAML"
        ) from error
    if not isinstance(value, dict):
        raise SourceCorrectionError("source correction manifest must be a YAML mapping")
    return value


def validate_source_correction(
    root: Path,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Validate the pinned correction manifest and every declared target."""

    root = root.resolve()
    path = manifest_path or root / MANIFEST_RELATIVE_PATH
    manifest = load_source_correction(path)
    _expect(
        sha256_file(path) == EXPECTED_MANIFEST_SHA256,
        "source correction manifest bytes differ from the pinned contract",
    )
    _expect_exact_keys(manifest, TOP_LEVEL_KEYS, "manifest")
    _expect(
        type(manifest["schema_version"]) is int and manifest["schema_version"] == 1,
        "schema_version must be integer 1",
    )
    _expect(manifest["kind"] == "immutable_source_correction_overlay", "overlay kind differs")
    _expect(manifest["issue"] == ISSUE_URL, "issue URL differs")
    _expect(manifest["created"] == CREATED, "overlay creation date differs")
    _expect(
        type(manifest["replacement_count"]) is int and manifest["replacement_count"] == 5,
        "replacement count differs",
    )
    changed_paths = _validate_changed_paths(manifest["changed_paths"])

    baseline = _mapping(manifest, "baseline")
    _expect_exact_keys(baseline, BASELINE_KEYS, "baseline")
    _expect(
        baseline["content_commit"] == BASELINE_CONTENT_COMMIT, "baseline content commit differs"
    )
    _expect(baseline["content_tree"] == BASELINE_CONTENT_TREE, "baseline content tree differs")
    _expect(
        baseline["migration_manifest"] == MIGRATION_MANIFEST_RELATIVE_PATH,
        "migration manifest path differs",
    )
    _expect(
        baseline["migration_manifest_sha256"] == MIGRATION_MANIFEST_SHA256,
        "migration manifest digest differs",
    )
    _expect(
        sha256_file(root / MIGRATION_MANIFEST_RELATIVE_PATH) == MIGRATION_MANIFEST_SHA256,
        "migration.yaml is not byte-identical to the immutable migration",
    )

    source = _mapping(manifest, "source")
    _expect_exact_keys(source, SOURCE_KEYS, "source")
    _expect(source["repository"] == SOURCE_REPOSITORY, "source repository differs")
    _expect(source["commit"] == SOURCE_COMMIT, "source commit differs")

    articles = manifest["articles"]
    _expect(
        isinstance(articles, list) and len(articles) == 1, "article correction row count differs"
    )
    article = _validate_article_row(root, articles[0])

    podcasts = manifest["podcasts"]
    _expect(
        isinstance(podcasts, list) and len(podcasts) == 1, "podcast correction row count differs"
    )
    podcast = _validate_podcast_row(root, podcasts[0])

    media_renames = manifest["media_renames"]
    _expect(
        isinstance(media_renames, list) and len(media_renames) == 1,
        "media rename row count differs",
    )
    media = _validate_media_row(root, media_renames[0])

    return {
        "manifest_sha256": sha256_file(path),
        "replacement_count": manifest["replacement_count"],
        "changed_paths": changed_paths,
        "article_corrections": {article["path"]: article},
        "podcast_corrections": {podcast["path"]: podcast},
        "media_renames": {media["old_path"]: media},
    }


def apply_article_url_corrections(source_bytes: bytes, row: dict[str, Any]) -> bytes:
    """Apply only complete Markdown/HTML link destinations declared by ``row``."""

    _expect(
        hashlib.sha256(source_bytes).hexdigest() == ARTICLE_LEGACY_SHA256,
        "article legacy digest differs",
    )
    _expect(git_blob_sha(source_bytes) == ARTICLE_LEGACY_BLOB, "article legacy blob differs")
    try:
        text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SourceCorrectionError("article source is not valid UTF-8") from error

    replacements = row.get("replacements")
    _expect(isinstance(replacements, list), "article replacements must be a list")
    result = text
    for ordinal, replacement in enumerate(replacements, start=1):
        prefix = f"article replacement {ordinal}"
        _expect(isinstance(replacement, dict), f"{prefix}: row must be a mapping")
        match_kind = replacement.get("match")
        old = replacement.get("old")
        new = replacement.get("new")
        _expect(match_kind in MATCH_KINDS, f"{prefix}: match kind is not allowed")
        _expect(isinstance(old, str) and isinstance(new, str), f"{prefix}: URLs must be strings")
        _expect(old != new, f"{prefix}: replacement must change the URL")
        matches = _link_matches(result, match_kind, old)
        expected_occurrences = replacement.get("occurrences")
        _expect(
            type(expected_occurrences) is int and expected_occurrences > 0,
            f"{prefix}: occurrence count is invalid",
        )
        _expect(
            len(matches) == expected_occurrences,
            f"{prefix}: complete link-destination count differs",
        )
        line_numbers = replacement.get("line_numbers")
        _expect(
            isinstance(line_numbers, list)
            and all(type(line) is int and line > 0 for line in line_numbers)
            and tuple(line_numbers) == tuple(match[2] for match in matches),
            f"{prefix}: line contexts differ",
        )
        for start, end, _ in reversed(matches):
            result = result[:start] + new + result[end:]

    corrected = result.encode("utf-8")
    _expect(
        hashlib.sha256(corrected).hexdigest() == ARTICLE_TARGET_SHA256,
        "article correction output digest differs",
    )
    return corrected


def _link_matches(text: str, match_kind: str, old: str) -> list[tuple[int, int, int]]:
    pattern = MARKDOWN_DESTINATION_RE if match_kind == "markdown_destination" else HTML_HREF_RE
    matches: list[tuple[int, int, int]] = []
    for match in pattern.finditer(text):
        url = match.group("url")
        if url == old:
            start, end = match.span("url")
            matches.append((start, end, text.count("\n", 0, start) + 1))
    return matches


def emit_source_correction_attestation(root: Path, commit_sha: str) -> dict[str, Any]:
    """Emit a deterministic attestation for a clean checked-out commit."""

    _expect(
        isinstance(commit_sha, str) and HEX_40.fullmatch(commit_sha) is not None,
        "replacement commit must be a lowercase 40-character SHA",
    )
    root = root.resolve()
    summary = validate_source_correction(root)
    head = _git_revision(root, "HEAD")
    _expect(head == commit_sha, "attestation commit does not match checkout HEAD")
    _expect(not _git_checkout_is_dirty(root), "attestation checkout is dirty")
    changed_paths = _git_changed_paths(root)
    _expect(
        changed_paths == summary["changed_paths"],
        "attestation changed-path census differs from the pinned contract",
    )
    tree = _git_revision(root, "HEAD^{tree}")
    article = summary["article_corrections"][ARTICLE_PATH]
    podcast = summary["podcast_corrections"][PODCAST_PATH]
    media = summary["media_renames"][MEDIA_OLD_PATH]
    return {
        "schema_version": 1,
        "kind": "immutable_source_correction_attestation",
        "replacement_commit": commit_sha,
        "replacement_tree": tree,
        "manifest": MANIFEST_RELATIVE_PATH.as_posix(),
        "manifest_sha256": summary["manifest_sha256"],
        "baseline_content_commit": BASELINE_CONTENT_COMMIT,
        "source_commit": SOURCE_COMMIT,
        "replacement_count": summary["replacement_count"],
        "changed_paths": [_changed_path_dict(item) for item in changed_paths],
        "corrections": {
            "articles": [article],
            "podcasts": [podcast],
            "media_renames": [media],
        },
        "files": [
            {"path": ARTICLE_PATH, "sha256": article["target_sha256"]},
            {"path": PODCAST_PATH, "sha256": podcast["target_sha256"]},
            {"path": MEDIA_NEW_PATH, "sha256": media["sha256"]},
        ],
    }


def _validate_changed_paths(value: Any) -> tuple[tuple[str, ...], ...]:
    _expect(isinstance(value, list), "changed paths must be a list")
    _expect(len(value) == len(EXPECTED_CHANGED_PATHS), "changed-path count differs")
    normalized: list[tuple[str, ...]] = []
    for ordinal, item in enumerate(value, start=1):
        prefix = f"changed path {ordinal}"
        _expect(isinstance(item, dict), f"{prefix}: row must be a mapping")
        status = item.get("status")
        _expect(status in {"A", "M", "R100"}, f"{prefix}: status is not allowed")
        if status == "R100":
            _expect_exact_keys(item, frozenset({"status", "old_path", "new_path"}), prefix)
            _canonical_path(item["old_path"], prefix)
            _canonical_path(item["new_path"], prefix)
            normalized.append((status, item["old_path"], item["new_path"]))
        else:
            _expect_exact_keys(item, frozenset({"status", "path"}), prefix)
            _canonical_path(item["path"], prefix)
            normalized.append((status, item["path"]))
    result = tuple(normalized)
    _expect(result == EXPECTED_CHANGED_PATHS, "changed-path contract differs")
    return result


def _changed_path_dict(item: tuple[str, ...]) -> dict[str, str]:
    if item[0] == "R100":
        return {"status": item[0], "old_path": item[1], "new_path": item[2]}
    return {"status": item[0], "path": item[1]}


def _validate_article_row(root: Path, row: Any) -> dict[str, Any]:
    prefix = "article 1"
    _expect(isinstance(row, dict), f"{prefix}: row must be a mapping")
    _expect_exact_keys(row, ARTICLE_KEYS, prefix)
    _expect(row["path"] == ARTICLE_PATH, f"{prefix}: path differs")
    _expect(row["legacy_path"] == ARTICLE_LEGACY_PATH, f"{prefix}: legacy path differs")
    _expect(_valid_hex(row["legacy_blob"], HEX_40), f"{prefix}: legacy blob is invalid")
    _expect(row["legacy_blob"] == ARTICLE_LEGACY_BLOB, f"{prefix}: legacy blob differs")
    _expect(_valid_hex(row["legacy_sha256"], HEX_64), f"{prefix}: legacy digest is invalid")
    _expect(row["legacy_sha256"] == ARTICLE_LEGACY_SHA256, f"{prefix}: legacy digest differs")
    _expect(_valid_hex(row["target_blob"], HEX_40), f"{prefix}: target blob is invalid")
    _expect(row["target_blob"] == ARTICLE_TARGET_BLOB, f"{prefix}: target blob differs")
    _expect(_valid_hex(row["target_sha256"], HEX_64), f"{prefix}: target digest is invalid")
    _expect(row["target_sha256"] == ARTICLE_TARGET_SHA256, f"{prefix}: target digest differs")
    _expect(
        type(row["replacement_count"]) is int and row["replacement_count"] == 5,
        f"{prefix}: replacement count differs",
    )
    replacements = row["replacements"]
    _expect(
        isinstance(replacements, list) and len(replacements) == len(EXPECTED_REPLACEMENTS),
        f"{prefix}: replacement row count differs",
    )
    normalized: list[dict[str, Any]] = []
    total = 0
    for ordinal, replacement in enumerate(replacements, start=1):
        replacement_prefix = f"{prefix} replacement {ordinal}"
        _expect(isinstance(replacement, dict), f"{replacement_prefix}: row must be a mapping")
        _expect_exact_keys(replacement, REPLACEMENT_KEYS, replacement_prefix)
        _expect(
            replacement["match"] in MATCH_KINDS, f"{replacement_prefix}: match kind is not allowed"
        )
        _expect(
            isinstance(replacement["old"], str)
            and isinstance(replacement["new"], str)
            and replacement["old"] != replacement["new"],
            f"{replacement_prefix}: URL values are invalid",
        )
        _expect(
            type(replacement["occurrences"]) is int and replacement["occurrences"] > 0,
            f"{replacement_prefix}: occurrence count is invalid",
        )
        expected_replacement = EXPECTED_REPLACEMENTS[ordinal - 1]
        _expect(
            replacement["occurrences"] == expected_replacement["occurrences"],
            f"{replacement_prefix}: occurrence contract differs",
        )
        lines = replacement["line_numbers"]
        _expect(
            isinstance(lines, list)
            and len(lines) == replacement["occurrences"]
            and all(type(line) is int and line > 0 for line in lines),
            f"{replacement_prefix}: line numbers are invalid",
        )
        normalized.append(
            {
                "match": replacement["match"],
                "old": replacement["old"],
                "new": replacement["new"],
                "occurrences": replacement["occurrences"],
                "line_numbers": tuple(lines),
            }
        )
        total += replacement["occurrences"]
    _expect(
        tuple(normalized) == EXPECTED_REPLACEMENTS,
        f"{prefix}: replacement contract differs",
    )
    _expect(total == 5, f"{prefix}: replacement total differs")
    target = _regular_file(root, ARTICLE_PATH, prefix)
    target_bytes = target.read_bytes()
    _expect(
        sha256_file(target) == ARTICLE_TARGET_SHA256,
        f"{prefix}: target digest differs",
    )
    _expect(
        git_blob_sha(target_bytes) == ARTICLE_TARGET_BLOB,
        f"{prefix}: target blob differs",
    )
    return row


def _validate_podcast_row(root: Path, row: Any) -> dict[str, Any]:
    prefix = "podcast 1"
    _expect(isinstance(row, dict), f"{prefix}: row must be a mapping")
    _expect_exact_keys(row, PODCAST_KEYS, prefix)
    expected = {
        "path": PODCAST_PATH,
        "legacy_path": PODCAST_LEGACY_PATH,
        "baseline_blob": PODCAST_BASELINE_BLOB,
        "baseline_sha256": PODCAST_BASELINE_SHA256,
        "target_blob": PODCAST_TARGET_BLOB,
        "target_sha256": PODCAST_TARGET_SHA256,
        "field": PODCAST_FIELD,
        "old": PODCAST_OLD_VALUE,
        "new": PODCAST_NEW_VALUE,
        "occurrences": 1,
    }
    for key, value in expected.items():
        _expect(row[key] == value, f"{prefix}: {key} differs")
    for key in ("baseline_blob", "target_blob"):
        _expect(_valid_hex(row[key], HEX_40), f"{prefix}: {key} is invalid")
    for key in ("baseline_sha256", "target_sha256"):
        _expect(_valid_hex(row[key], HEX_64), f"{prefix}: {key} is invalid")
    _expect(
        type(row["occurrences"]) is int and row["occurrences"] == 1, f"{prefix}: occurrences differ"
    )
    target = _regular_file(root, PODCAST_PATH, prefix)
    target_bytes = target.read_bytes()
    _expect(sha256_file(target) == PODCAST_TARGET_SHA256, f"{prefix}: target digest differs")
    _expect(git_blob_sha(target_bytes) == PODCAST_TARGET_BLOB, f"{prefix}: target blob differs")
    try:
        value = yaml.safe_load(target_bytes)
    except (UnicodeError, yaml.YAMLError) as error:
        raise SourceCorrectionError(f"{prefix}: target is unreadable or invalid YAML") from error
    _expect(isinstance(value, dict), f"{prefix}: target must be a YAML mapping")
    _expect(value.get(PODCAST_FIELD) == PODCAST_NEW_VALUE, f"{prefix}: corrected scalar differs")
    _expect(
        target_bytes.count(PODCAST_NEW_VALUE.encode("utf-8")) == 1,
        f"{prefix}: corrected scalar occurrence count differs",
    )
    return row


def _validate_media_row(root: Path, row: Any) -> dict[str, Any]:
    prefix = "media rename 1"
    _expect(isinstance(row, dict), f"{prefix}: row must be a mapping")
    _expect_exact_keys(row, MEDIA_KEYS, prefix)
    expected = {
        "old_path": MEDIA_OLD_PATH,
        "new_path": MEDIA_NEW_PATH,
        "blob": MEDIA_BLOB,
        "sha256": MEDIA_SHA256,
        "bytes": MEDIA_BYTES,
    }
    for key, value in expected.items():
        _expect(row[key] == value, f"{prefix}: {key} differs")
    _expect(_valid_hex(row["blob"], HEX_40), f"{prefix}: blob is invalid")
    _expect(_valid_hex(row["sha256"], HEX_64), f"{prefix}: digest is invalid")
    _expect(type(row["bytes"]) is int and row["bytes"] > 0, f"{prefix}: byte count is invalid")
    new_path = _regular_file(root, MEDIA_NEW_PATH, prefix)
    data = new_path.read_bytes()
    _expect(len(data) == MEDIA_BYTES, f"{prefix}: byte count differs")
    _expect(hashlib.sha256(data).hexdigest() == MEDIA_SHA256, f"{prefix}: digest differs")
    _expect(git_blob_sha(data) == MEDIA_BLOB, f"{prefix}: blob differs")
    old_path = root / MEDIA_OLD_PATH
    try:
        old_path.lstat()
    except FileNotFoundError:
        pass
    except OSError as error:
        raise SourceCorrectionError(f"{prefix}: old media path is unreadable") from error
    else:
        raise SourceCorrectionError(f"{prefix}: old media path still exists")
    return row


def _regular_file(root: Path, relative: str, prefix: str) -> Path:
    _expect(_canonical_path(relative, prefix), f"{prefix}: path is not canonical")
    current = root
    try:
        for part in relative.split("/"):
            current = current / part
            metadata = current.lstat()
            _expect(not stat.S_ISLNK(metadata.st_mode), f"{prefix}: target is a symlink")
    except FileNotFoundError as error:
        raise SourceCorrectionError(f"{prefix}: target file is missing") from error
    except OSError as error:
        raise SourceCorrectionError(f"{prefix}: target is unreadable") from error
    _expect(stat.S_ISREG(metadata.st_mode), f"{prefix}: target is not a regular file")
    return current


def _canonical_path(value: Any, prefix: str) -> bool:
    _expect(isinstance(value, str) and bool(value), f"{prefix}: path must be a string")
    _expect("\\" not in value, f"{prefix}: path is not canonical")
    path = PurePosixPath(value)
    _expect(
        not path.is_absolute()
        and all(part not in {"", ".", ".."} for part in value.split("/"))
        and path.as_posix() == value,
        f"{prefix}: path is not canonical",
    )
    return True


def _valid_hex(value: Any, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _mapping(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise SourceCorrectionError(f"{key} must be a mapping")
    return result


def _expect_exact_keys(value: dict[str, Any], expected: frozenset[str], prefix: str) -> None:
    _expect(set(value) == expected, f"{prefix}: schema keys differ")


def _expect(condition: object, message: str) -> None:
    if not condition:
        raise SourceCorrectionError(message)


def _git_revision(root: Path, revision: str) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", revision],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise SourceCorrectionError("unable to resolve attestation checkout revision") from error
    value = result.stdout.strip()
    _expect(HEX_40.fullmatch(value) is not None, "attestation checkout revision is invalid")
    return value


def _git_changed_paths(root: Path) -> tuple[tuple[str, ...], ...]:
    try:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-status",
                "--find-renames=100%",
                f"{BASELINE_CONTENT_COMMIT}..HEAD",
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise SourceCorrectionError("unable to compute source correction path census") from error
    normalized: list[tuple[str, ...]] = []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        status = fields[0]
        if status == "R100":
            _expect(len(fields) == 3, "source correction rename census is malformed")
            normalized.append((status, fields[1], fields[2]))
        else:
            _expect(
                status in {"A", "M"} and len(fields) == 2,
                "source correction path census is malformed",
            )
            normalized.append((status, fields[1]))
    return tuple(normalized)


def _git_checkout_is_dirty(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise SourceCorrectionError("unable to inspect attestation checkout status") from error
    return bool(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the immutable source correction overlay")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--attest-commit")
    parser.add_argument("--attestation-output", type=Path)
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        if args.attest_commit:
            _expect(
                args.attestation_output is not None,
                "attestation output is required",
            )
            attestation = emit_source_correction_attestation(root, args.attest_commit)
            rendered = json.dumps(attestation, indent=2, sort_keys=True) + "\n"
            args.attestation_output.parent.mkdir(parents=True, exist_ok=True)
            args.attestation_output.write_text(rendered, encoding="utf-8")
            print(
                "PASS: "
                f"commit={attestation['replacement_commit']}, "
                f"tree={attestation['replacement_tree']}, "
                f"manifest_sha256={attestation['manifest_sha256']}"
            )
            return 0
        summary = validate_source_correction(root)
    except (OSError, SourceCorrectionError) as error:
        print(f"STOP: {error}")
        return 1
    print(
        "PASS: "
        f"replacements={summary['replacement_count']}, "
        f"manifest_sha256={summary['manifest_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
