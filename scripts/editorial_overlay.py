from __future__ import annotations

import argparse
import hashlib
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

MANIFEST_RELATIVE_PATH = Path("editorial-overlays/2026-08-10-podcast-descriptions.yaml")
EXPECTED_MANIFEST_SHA256 = "4ab314d8376e9d6079d362f5812621fb3bcaded35584bb32a591b1afc806081a"
ISSUE_URL = "https://github.com/DataTalksClub/content/issues/3"
CREATED = "2026-08-10"
BASELINE_CONTENT_COMMIT = "b9a40ba974fdef67ee3a2a70f114734f2581033c"
SOURCE_REPOSITORY = "https://github.com/DataTalksClub/datatalksclub.github.io"
SOURCE_COMMIT = "ee43d3fa0929faf691178d79f19528e6f15a83e5"
MIGRATION_MANIFEST_SHA256 = "dd78a343a5f387a74afa914fc6c7e19790e202aa5d6fa9aba08bfda5995c5f86"
HEX_64 = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_TARGETS = (
    "podcasts/_s12e08.yaml",
    "podcasts/data-team-roles.yaml",
    "podcasts/machine-learning-data-science-interview-prep.yaml",
    "podcasts/s22e06-from-black-box-systems-to-augmented-decision-making.yaml",
    "podcasts/s22e07-reinventing-career-in-tech.yaml",
    "podcasts/s22e08-building-pet-health-tech-ml-sensors-and-dog-behavior-data.yaml",
    "podcasts/s23e01-ai-engineering-skill-stack-agents-llmops-and-how-to-ship-ai-products.yaml",
    "podcasts/s23e02-foundations-of-analytics-engineer-role-skills-scope-and-modern-practices.yaml",
    "podcasts/s23e03-future-of-ai-agents.yaml",
    "podcasts/s23e04-how-to-become-ai-engineer-after-career-break.yaml",
    "podcasts/s23e05-inside-ai-engineer-role-tools-skills-and-career-path.yaml",
    (
        "podcasts/s23e06-data-engineer-career-in-2026-roles-specializations-and-"
        "what-companies-look-for.yaml"
    ),
    "podcasts/s23e07-understanding-ai-engineer-role.yaml",
    "podcasts/s23e09-starting-data-conference-data-makers-fest-story.yaml",
    "podcasts/s24e01-competitions-beyond-kaggle-leaderboard.yaml",
    "podcasts/s24e03-from-notebook-to-production-building-end-to-end-ai-systems.yaml",
    "podcasts/s24e04-from-genai-pilots-to-production.yaml",
    "podcasts/s24e05-ai-adoption-in-enterprise-beyond-writing-code.yaml",
    "podcasts/s24e06-how-to-build-ai-that-actually-ships-in-production.yaml",
)

TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "kind",
        "issue",
        "created",
        "baseline_content_commit",
        "source",
        "migration",
        "field",
        "target_count",
        "targets",
    }
)
SOURCE_KEYS = frozenset({"repository", "commit"})
MIGRATION_KEYS = frozenset({"manifest", "sha256"})
TARGET_KEYS = frozenset({"path", "key", "description_sha256", "target_sha256"})


class EditorialOverlayError(ValueError):
    """A bounded, content-free editorial overlay validation failure."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_editorial_overlay(path: Path) -> dict[str, Any]:
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise EditorialOverlayError("editorial overlay manifest is not a regular file")
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except EditorialOverlayError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise EditorialOverlayError(
            "editorial overlay manifest is unreadable or invalid YAML"
        ) from error
    if not isinstance(value, dict):
        raise EditorialOverlayError("editorial overlay manifest must be a YAML mapping")
    return value


def validate_editorial_overlay(
    root: Path,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    path = manifest_path or root / MANIFEST_RELATIVE_PATH
    manifest = load_editorial_overlay(path)

    _expect(
        sha256_file(path) == EXPECTED_MANIFEST_SHA256,
        "editorial overlay manifest bytes differ from the pinned contract",
    )
    _expect_exact_keys(manifest, TOP_LEVEL_KEYS, "manifest")
    _expect(
        type(manifest["schema_version"]) is int and manifest["schema_version"] == 1,
        "schema_version must be integer 1",
    )
    _expect(
        manifest["kind"] == "podcast_description_editorial_overlay",
        "overlay kind differs",
    )
    _expect(manifest["issue"] == ISSUE_URL, "issue URL differs")
    _expect(manifest["created"] == CREATED, "overlay creation date differs")
    _expect(
        manifest["baseline_content_commit"] == BASELINE_CONTENT_COMMIT,
        "baseline content commit differs",
    )

    source = _mapping(manifest, "source")
    _expect_exact_keys(source, SOURCE_KEYS, "source")
    _expect(source["repository"] == SOURCE_REPOSITORY, "source repository differs")
    _expect(source["commit"] == SOURCE_COMMIT, "source commit differs")

    migration = _mapping(manifest, "migration")
    _expect_exact_keys(migration, MIGRATION_KEYS, "migration")
    _expect(migration["manifest"] == "migration.yaml", "migration manifest path differs")
    _expect(
        migration["sha256"] == MIGRATION_MANIFEST_SHA256,
        "migration manifest digest differs",
    )
    _expect(
        sha256_file(root / "migration.yaml") == MIGRATION_MANIFEST_SHA256,
        "migration.yaml is not byte-identical to the immutable migration",
    )

    _expect(manifest["field"] == "description", "overlay field differs")
    _expect(manifest["target_count"] == len(EXPECTED_TARGETS), "target count differs")
    targets = manifest["targets"]
    _expect(isinstance(targets, list), "targets must be a list")
    _expect(len(targets) == len(EXPECTED_TARGETS), "target row count differs")

    descriptions: dict[str, str] = {}
    ordered_paths: list[str] = []
    for ordinal, row in enumerate(targets, start=1):
        prefix = f"target {ordinal}"
        _expect(isinstance(row, dict), f"{prefix}: row must be a mapping")
        _expect_exact_keys(row, TARGET_KEYS, prefix)
        relative = _canonical_target_path(row["path"], prefix)
        _expect(relative not in descriptions, f"{prefix}: duplicate target path")
        _expect(row["key"] == "description", f"{prefix}: key must be description")
        for digest_key in ("description_sha256", "target_sha256"):
            _expect(
                isinstance(row[digest_key], str) and HEX_64.fullmatch(row[digest_key]),
                f"{prefix}: {digest_key} is invalid",
            )

        target_path = _regular_target(root, relative, prefix)
        try:
            target_bytes = target_path.read_bytes()
            value = yaml.safe_load(target_bytes)
        except (OSError, UnicodeError, yaml.YAMLError) as error:
            raise EditorialOverlayError(
                f"{prefix}: target is unreadable or invalid YAML"
            ) from error
        _expect(isinstance(value, dict), f"{prefix}: target must be a YAML mapping")
        description = value.get("description")
        _expect(
            isinstance(description, str) and bool(description.strip()),
            f"{prefix}: description must be a non-empty string",
        )
        _expect(
            hashlib.sha256(description.encode("utf-8")).hexdigest() == row["description_sha256"],
            f"{prefix}: description digest differs",
        )
        _expect(
            hashlib.sha256(target_bytes).hexdigest() == row["target_sha256"],
            f"{prefix}: target content digest differs",
        )
        descriptions[relative] = description
        ordered_paths.append(relative)

    _expect(set(ordered_paths) == set(EXPECTED_TARGETS), "overlay target path set differs")
    _expect(tuple(ordered_paths) == EXPECTED_TARGETS, "overlay target order differs")
    return {
        "targets": len(descriptions),
        "field": "description",
        "source_commit": SOURCE_COMMIT,
        "manifest_sha256": sha256_file(path),
        "descriptions": descriptions,
    }


def _canonical_target_path(value: Any, prefix: str) -> str:
    _expect(isinstance(value, str) and bool(value), f"{prefix}: path must be a string")
    _expect("\\" not in value, f"{prefix}: target path is not canonical")
    raw_parts = value.split("/")
    _expect(
        len(raw_parts) == 2
        and raw_parts[0] == "podcasts"
        and raw_parts[1] not in {"", ".", ".."}
        and value == PurePosixPath(value).as_posix()
        and PurePosixPath(value).suffix == ".yaml",
        f"{prefix}: target path is not canonical",
    )
    return value


def _regular_target(root: Path, relative: str, prefix: str) -> Path:
    current = root
    try:
        for part in relative.split("/"):
            current = current / part
            metadata = current.lstat()
            _expect(not stat.S_ISLNK(metadata.st_mode), f"{prefix}: target is a symlink")
    except FileNotFoundError as error:
        raise EditorialOverlayError(f"{prefix}: target file is missing") from error
    except OSError as error:
        raise EditorialOverlayError(f"{prefix}: target is unreadable") from error
    _expect(stat.S_ISREG(metadata.st_mode), f"{prefix}: target is not a regular file")
    return current


def _mapping(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise EditorialOverlayError(f"{key} must be a mapping")
    return result


def _expect_exact_keys(value: dict[str, Any], expected: frozenset[str], prefix: str) -> None:
    _expect(set(value) == expected, f"{prefix}: schema keys differ")


def _expect(condition: object, message: str) -> None:
    if not condition:
        raise EditorialOverlayError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate podcast description editorial overlay")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        summary = validate_editorial_overlay(args.root.resolve())
    except (OSError, EditorialOverlayError) as error:
        print(f"STOP: {error}")
        return 1
    print(
        "PASS: "
        f"targets={summary['targets']}, "
        f"field={summary['field']}, "
        f"source_commit={summary['source_commit']}, "
        f"manifest_sha256={summary['manifest_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
