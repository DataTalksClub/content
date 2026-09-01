from __future__ import annotations

import argparse
import hashlib
import stat
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

MANIFEST_RELATIVE_PATH = Path("migration/podcast-removals.yaml")
MIGRATION_MANIFEST_RELATIVE_PATH = Path("migration/migration.yaml")
EXPECTED_MANIFEST_SHA256 = "d639d152d7c6b2d726da15972270f1c4402f3a4a3ebf91674e8158991da1b6ae"
MIGRATION_MANIFEST_SHA256 = "dd78a343a5f387a74afa914fc6c7e19790e202aa5d6fa9aba08bfda5995c5f86"
SOURCE_REPOSITORY = "https://github.com/DataTalksClub/datatalksclub.github.io"
SOURCE_COMMIT = "ee43d3fa0929faf691178d79f19528e6f15a83e5"
BASELINE_COUNTS = {"podcasts": 205, "podcast_transcripts": 203}
CURRENT_COUNTS = {"podcasts": 203, "podcast_transcripts": 201}

EXPECTED_REMOVALS = (
    {
        "source": "_podcast/_s12e08.md",
        "records": ["podcasts/_s12e08.yaml", "podcasts/s12/e08.yaml"],
        "transcripts": [
            "podcasts/transcripts/_s12e08.yaml",
            "podcasts/s12/e08-transcript.yaml",
        ],
    },
    {
        "source": "_podcast/_theme-park-crowd-modeling-to-tesla-full-stack-data-engineering.md",
        "records": [
            "podcasts/_theme-park-crowd-modeling-to-tesla-full-stack-data-engineering.yaml",
            "podcasts/s21/e09.yaml",
        ],
        "transcripts": [
            "podcasts/transcripts/_theme-park-crowd-modeling-to-tesla-full-stack-data-engineering.yaml",
            "podcasts/s21/e09-transcript.yaml",
        ],
    },
)

TOP_LEVEL_KEYS = frozenset({"schema_version", "kind", "created", "baseline", "current", "removals"})
BASELINE_KEYS = frozenset(
    {
        "migration_manifest",
        "migration_manifest_sha256",
        "source_repository",
        "source_commit",
        "counts",
    }
)
CURRENT_KEYS = frozenset({"counts"})
COUNT_KEYS = frozenset({"podcasts", "podcast_transcripts"})
REMOVAL_KEYS = frozenset({"source", "records", "transcripts"})


class RemovalManifestError(ValueError):
    """A bounded, path-specific podcast removal manifest failure."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_removal_manifest(path: Path) -> dict[str, Any]:
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise RemovalManifestError("podcast removal manifest is not a regular file")
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except RemovalManifestError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise RemovalManifestError(
            "podcast removal manifest is unreadable or invalid YAML"
        ) from error
    if not isinstance(value, dict):
        raise RemovalManifestError("podcast removal manifest must be a YAML mapping")
    return value


def removal_source_paths(path: Path) -> frozenset[str]:
    manifest = load_removal_manifest(path)
    removals = manifest.get("removals")
    if not isinstance(removals, list) or any(not isinstance(row, dict) for row in removals):
        raise RemovalManifestError("podcast removal manifest removals must be mappings")
    sources = {row.get("source") for row in removals}
    if not all(isinstance(source, str) for source in sources):
        raise RemovalManifestError("podcast removal source paths must be strings")
    return frozenset(sources)


def validate_removal_manifest(
    root: Path,
    manifest_path: Path | None = None,
    *,
    check_repository_counts: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    path = manifest_path or root / MANIFEST_RELATIVE_PATH
    manifest = load_removal_manifest(path)

    _expect(
        sha256_file(path) == EXPECTED_MANIFEST_SHA256,
        "podcast removal manifest bytes differ from the pinned contract",
    )
    _expect_exact_keys(manifest, TOP_LEVEL_KEYS, "manifest")
    _expect(
        type(manifest["schema_version"]) is int and manifest["schema_version"] == 1,
        "schema_version must be integer 1",
    )
    _expect(manifest["kind"] == "podcast_guest_removal", "removal manifest kind differs")
    _expect(manifest["created"] == "2026-09-01", "removal manifest creation date differs")

    baseline = _mapping(manifest, "baseline")
    _expect_exact_keys(baseline, BASELINE_KEYS, "baseline")
    _expect(
        baseline["migration_manifest"] == MIGRATION_MANIFEST_RELATIVE_PATH.as_posix(),
        "baseline migration manifest path differs",
    )
    _expect(
        baseline["migration_manifest_sha256"] == MIGRATION_MANIFEST_SHA256,
        "baseline migration manifest digest differs",
    )
    _expect(baseline["source_repository"] == SOURCE_REPOSITORY, "source repository differs")
    _expect(baseline["source_commit"] == SOURCE_COMMIT, "source commit differs")
    _validate_counts(baseline["counts"], BASELINE_COUNTS, "baseline counts")
    _expect(
        sha256_file(root / MIGRATION_MANIFEST_RELATIVE_PATH) == MIGRATION_MANIFEST_SHA256,
        "migration manifest is not byte-identical to the immutable baseline",
    )

    current = _mapping(manifest, "current")
    _expect_exact_keys(current, CURRENT_KEYS, "current")
    _validate_counts(current["counts"], CURRENT_COUNTS, "current counts")

    removals = manifest["removals"]
    _expect(isinstance(removals, list), "removals must be a list")
    _expect(len(removals) == len(EXPECTED_REMOVALS), "removal count differs")
    removed_slugs: set[str] = set()
    for ordinal, (row, expected) in enumerate(
        zip(removals, EXPECTED_REMOVALS, strict=True), start=1
    ):
        prefix = f"removal {ordinal}"
        _expect(isinstance(row, dict), f"{prefix}: row must be a mapping")
        _expect_exact_keys(row, REMOVAL_KEYS, prefix)
        _expect(row == expected, f"{prefix}: removal differs from the pinned request")
        source = _canonical_source_path(row["source"], prefix)
        records = row["records"]
        transcripts = row["transcripts"]
        _expect(isinstance(records, list), f"{prefix}: records must be a list")
        _expect(isinstance(transcripts, list), f"{prefix}: transcripts must be a list")
        _expect(records and transcripts, f"{prefix}: records and transcripts cannot be empty")
        slug = Path(source).stem
        _expect(slug not in removed_slugs, f"{prefix}: duplicate source slug")
        removed_slugs.add(slug)
        for ordinal_path, record in enumerate(records, start=1):
            record_prefix = f"{prefix}: record {ordinal_path}"
            _canonical_target_path(record, record_prefix, "record")
            _expect_absent(root / record, f"{record_prefix} is present")
        for ordinal_path, transcript in enumerate(transcripts, start=1):
            transcript_prefix = f"{prefix}: transcript {ordinal_path}"
            _canonical_target_path(transcript, transcript_prefix, "transcript")
            _expect_absent(root / transcript, f"{transcript_prefix} is present")

    if check_repository_counts:
        actual_counts = _repository_counts(root)
        _expect(actual_counts == CURRENT_COUNTS, "repository counts differ from removal manifest")
        _expect_no_removed_records(root / "podcasts", removed_slugs)

    return {
        "removals": len(removals),
        "sources": frozenset(row["source"] for row in removals),
        "slugs": frozenset(removed_slugs),
        "records": frozenset(record for row in removals for record in row["records"]),
        "transcripts": frozenset(
            transcript for row in removals for transcript in row["transcripts"]
        ),
        "baseline_counts": dict(BASELINE_COUNTS),
        "current_counts": dict(CURRENT_COUNTS),
        "source_commit": SOURCE_COMMIT,
        "manifest_sha256": sha256_file(path),
    }


def _repository_counts(root: Path) -> dict[str, int]:
    podcasts = 0
    transcripts = 0
    for path in (root / "podcasts").rglob("*.yaml"):
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as error:
            raise RemovalManifestError(f"{path}: cannot inspect podcast removal state") from error
        if not isinstance(value, dict):
            continue
        if "slug" in value:
            podcasts += 1
        elif "podcast" in value:
            transcripts += 1
    return {"podcasts": podcasts, "podcast_transcripts": transcripts}


def _expect_no_removed_records(podcasts_dir: Path, removed_slugs: set[str]) -> None:
    if not podcasts_dir.is_dir():
        raise RemovalManifestError("podcasts directory is missing")
    for path in sorted(podcasts_dir.rglob("*.yaml")):
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as error:
            raise RemovalManifestError(f"{path}: cannot inspect podcast removal state") from error
        if not isinstance(value, dict):
            continue
        if value.get("slug") in removed_slugs or value.get("podcast") in removed_slugs:
            raise RemovalManifestError(f"{path}: removed podcast is present")


def _canonical_source_path(value: Any, prefix: str) -> str:
    _expect(isinstance(value, str) and bool(value), f"{prefix}: source must be a string")
    path = PurePosixPath(value)
    _expect(
        "\\" not in value
        and value == path.as_posix()
        and len(path.parts) == 2
        and path.parts[0] == "_podcast"
        and path.suffix == ".md"
        and all(part not in {"", ".", ".."} for part in path.parts),
        f"{prefix}: source path is not canonical",
    )
    return value


def _canonical_target_path(value: Any, prefix: str, kind: str) -> str:
    _expect(isinstance(value, str) and bool(value), f"{prefix}: {kind} must be a string")
    path = PurePosixPath(value)
    expected_parts = ("podcasts",) if kind == "record" else ("podcasts", "transcripts")
    is_legacy = len(path.parts) == len(expected_parts) + 1 and path.parts[:-1] == expected_parts
    is_seasonal = (
        len(path.parts) == 3
        and path.parts[0] == "podcasts"
        and path.parts[1].startswith("s")
        and path.parts[1][1:].isdigit()
    )
    _expect(
        "\\" not in value
        and value == path.as_posix()
        and (is_legacy or is_seasonal)
        and path.parts[-1] not in {"", ".", ".."}
        and path.suffix == ".yaml",
        f"{prefix}: {kind} path is not canonical",
    )
    return value


def _validate_counts(value: Any, expected: dict[str, int], prefix: str) -> None:
    _expect(isinstance(value, dict), f"{prefix} must be a mapping")
    _expect_exact_keys(value, COUNT_KEYS, prefix)
    _expect(value == expected, f"{prefix} differ")


def _expect_absent(path: Path, message: str) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise RemovalManifestError(f"{path}: cannot inspect removal state") from error
    raise RemovalManifestError(message)


def _mapping(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise RemovalManifestError(f"{key} must be a mapping")
    return result


def _expect_exact_keys(value: dict[str, Any], expected: frozenset[str], prefix: str) -> None:
    _expect(set(value) == expected, f"{prefix}: schema keys differ")


def _expect(condition: object, message: str) -> None:
    if not condition:
        raise RemovalManifestError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate podcast guest-removal provenance")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        summary = validate_removal_manifest(args.root.resolve())
    except (OSError, RemovalManifestError) as error:
        print(f"STOP: {error}")
        return 1
    print(
        "PASS: "
        f"removals={summary['removals']}, "
        f"podcasts={summary['current_counts']['podcasts']}, "
        f"transcripts={summary['current_counts']['podcast_transcripts']}, "
        f"manifest_sha256={summary['manifest_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
