from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import struct
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from scripts.validate_content import (
    ALLOWED_MEDIA_EXTENSIONS,
    _media_signature_error,
    load_article_front_matter,
    load_yaml_mapping,
)

MANIFEST_RELATIVE_PATH = Path("repairs/2026-08-09-missing-media.yaml")
BASELINE_COMMIT = "373bef2912342ece1d2a2d2a9395aa3417243283"
LEGACY_COMMIT = "ee43d3fa0929faf691178d79f19528e6f15a83e5"
MIGRATION_MANIFEST_SHA256 = "dd78a343a5f387a74afa914fc6c7e19790e202aa5d6fa9aba08bfda5995c5f86"
EXPECTED_MANIFEST_SHA256 = "80d3014c47bf57de792473fc1da8f7569daeb55107688c3485153f773948d3aa"
EXPECTED_GENERATION_DIGEST = "d03e51678147f064d628a443d558e69e9e586cad4ee90659fef6e3e495322013"
EDITOR_COMMENT_URL = "https://github.com/DataTalksClub/content/issues/2#issuecomment-5230732231"
EDITOR_APPROVER = "alexeygrigorev"
EDITOR_APPROVED_AT = "2026-08-09T09:08:34Z"
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_COUNTS = {
    "articles": 55,
    "podcasts": 205,
    "podcast_transcripts": 203,
    "books": 98,
    "media": 815,
}
EXPECTED_DELTA = {
    "articles": 0,
    "podcasts": 0,
    "podcast_transcripts": 0,
    "books": 0,
    "media": 8,
}
EXPECTED_INVARIANTS = [
    "migration.yaml remains byte-identical to the baseline",
    "only the two declared article image scalars change",
    "all 807 baseline media files remain byte-identical",
    "article bodies remain byte-identical",
    "podcast metadata and transcripts remain unchanged",
    "book metadata summaries and archives remain unchanged",
]
EXPECTED_REPAIRS: tuple[dict[str, Any], ...] = (
    {
        "record": "articles/2022-07-12-building-data-science-team.md",
        "baseline_blob": "9bedeba44c6668650fce34288945bc7b147727a9",
        "action": "restore_identical",
        "result": "images/posts/2022-07-12-building-data-science-team/cover.jpg",
        "result_sha256": "9961d52e08c39164dc4da47062597a87e15551bc45b43183017d8e4eccfc158f",
        "row_digest": "4b057b4e58d9b386fb82de6319c3248b7d006c0570fc60d747afef00b9017e0f",
        "added": True,
    },
    {
        "record": "articles/2025-05-16-datatalks-club-community-demographics.md",
        "baseline_blob": "da9606c8a58bff805f1ef44b5925b3e7756fb540",
        "action": "generate_standard_post_preview",
        "result": ("images/posts/2025-05-16-datatalks-club-community-demographics/cover.jpg"),
        "result_sha256": "b9db7ac7f02e84cc30d14d60ec6ed922f296e6920bc1723bb7edba4ca5f90c82",
        "row_digest": "acc72d3c6ea2834503a939a2084eacf748effc76f6d56b4345d9a6f7cc1ef7d8",
        "added": True,
    },
    {
        "record": (
            "articles/2025-08-05-how-to-build-waste-classifier-case-study-from-ml-zoomcamp.md"
        ),
        "baseline_blob": "9dccb2ff7f37a1cd0979a1a90c5b5fc6812f4975",
        "action": "generate_standard_post_preview",
        "result": (
            "images/posts/2025-08-05-how-to-build-waste-classifier-case-study-from-"
            "ml-zoomcamp/cover.jpg"
        ),
        "result_sha256": "072faeefaaf950e16337ef1fd9c7ab23370b8e61965d139aa3e8ae33eb2537af",
        "row_digest": "cf87ea18ad99bb48d1febed0bfce98f62bd6989af1db4c9f31eca0360af1143f",
        "added": True,
        "preview_title_override": "Building a Waste Classifier",
    },
    {
        "record": "articles/2025-08-05-key-lessons-from-ml-zoomcamp-serena-haidar.md",
        "baseline_blob": "2792ccffe00ecd0264e838a046c2d9befa7d0c5f",
        "action": "generate_standard_post_preview",
        "result": ("images/posts/2025-08-05-key-lessons-from-ml-zoomcamp-serena-haidar/cover.jpg"),
        "result_sha256": "b31bacc143b60728f9becb8c5fa602bb6dfb58e3e42c88bb22edb619a986d7ff",
        "row_digest": "d0f297e30c77a53a160d69236e633580662cb2be636bdae1871e954349d8b71b",
        "added": True,
    },
    {
        "record": (
            "articles/2025-08-11-building-discipline-in-machine-learning-with-ml-zoomcamp.md"
        ),
        "baseline_blob": "cc2ef11edd08f8fcc9230288b338734bee5e43e7",
        "action": "generate_standard_post_preview",
        "result": (
            "images/posts/2025-08-11-tab-2-building-discipline-in-machine-learning-"
            "with-ml-zoomcamp/cover.jpg"
        ),
        "result_sha256": "929bef77044dd413aa575a65266ea6d4676af172c920394ab2f9fb380ca5c988",
        "row_digest": "411afe70daef5d330fec1151f911263518534b243641535fb9ecfa3cf20c8515",
        "added": True,
    },
    {
        "record": (
            "articles/2025-08-11-how-to-build-blood-cell-classifier-for-cancer-"
            "prediction-case-study-from-ml-zoomcamp.md"
        ),
        "baseline_blob": "c63682ad65661a2dec4f6cc422c9d2cb2113f46d",
        "action": "generate_standard_post_preview",
        "result": (
            "images/posts/2025-08-11-tab-1-how-to-build-blood-cell-classifier-for-"
            "cancer-prediction-case-study-from-ml-zoomcamp/cover.jpg"
        ),
        "result_sha256": "be2d6051433b159014b8bfddcf22d54888956af047505b786be2309c87c2d883",
        "row_digest": "d5afbc79ec62a166c0381971c02fe4edec0542fd609f03ac58d0d024c7b9765e",
        "added": True,
        "preview_title_override": "Building a Blood Cell Classifier",
    },
    {
        "record": "articles/2025-12-10-free-data-engineering-courses.md",
        "baseline_blob": "81cf6a474b9bf7e661461eac42ac1402e1f24929",
        "action": "correct_image_path",
        "result": "images/posts/2025-12-10-free-data-engineering-courses/cover.png",
        "result_sha256": "b2a9dc3fe73b9c3c7d23eb2893df6cfb6507629e7c5e8523a18dca194c676b9c",
        "row_digest": "a3ba56755cb4367f86c3b4feeaf51313001144976a8883162960996b0969e7e1",
        "added": False,
        "old_value": "images/posts/2023-11-18-data-engineering-zoomcamp/cover.png",
        "new_value": "images/posts/2025-12-10-free-data-engineering-courses/cover.png",
    },
    {
        "record": "articles/2026-01-25-benefits-of-learning-in-public.md",
        "baseline_blob": "7215821b5332ee61fee05395e84ef035f55100d4",
        "action": "correct_image_path",
        "result": (
            "images/posts/2026-03-05-benefits-of-learning-in-public-and-why-it-works/cover.jpg"
        ),
        "result_sha256": "14eec4d894d5de59e0258dad2aeb52673bd8e76c3c1e6d0213cbeeb01522c17e",
        "row_digest": "ebe5e66efb478e64738f88026377bd08765ec91c217eab17b124036524740c33",
        "added": False,
        "old_value": (
            "images/posts/2026-01-25-benefits-of-learning-in-public-and-why-it-works/cover.jpg"
        ),
        "new_value": (
            "images/posts/2026-03-05-benefits-of-learning-in-public-and-why-it-works/cover.jpg"
        ),
    },
    {
        "record": "books/20241104-llm-engineer-s-handbook.yaml",
        "baseline_blob": "1485e55a615dff7178ff0aff689e442c91949fc5",
        "action": "generate_standard_book_preview",
        "result": "images/books/20241104-llm-engineer-s-handbook/preview.jpg",
        "result_sha256": "e1d03041ec8b93b2399215b6ffb53c85f19054022b16ad10638cbe8b820b174b",
        "row_digest": "de3c06439eb17029eb426f6cc9cc41257f3b06e34f51f7fc2f3a4cb353e7ac21",
        "added": True,
    },
    {
        "record": "podcasts/ai-for-ecology-biodiversity-and-conservation.yaml",
        "baseline_blob": "f7812500431622e3667bd85991e5bdbe55c5b583",
        "action": "generate_standard_podcast_preview",
        "result": "images/podcast/ai-for-ecology-biodiversity-and-conservation.jpg",
        "result_sha256": "83323cd39740fc051426b7a6f47c8235158161cbd9957546187e1b64333b2674",
        "row_digest": "f6d73049a4a0aef8bdebde7e3a4ec7a99a38caad5695f9e78741bc5f4ea8ac3d",
        "added": True,
    },
)
GENERATED_ACTIONS = frozenset(
    {
        "generate_standard_post_preview",
        "generate_standard_book_preview",
        "generate_standard_podcast_preview",
    }
)


class RepairManifestError(ValueError):
    """A bounded, content-free repair provenance failure."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_repair_manifest(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise RepairManifestError("repair manifest is unreadable or invalid YAML") from error
    if not isinstance(value, dict):
        raise RepairManifestError("repair manifest must be a YAML mapping")
    return value


def validate_repair_manifest(
    root: Path,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    path = manifest_path or root / MANIFEST_RELATIVE_PATH
    manifest = load_repair_manifest(path)

    _expect(
        sha256_file(path) == EXPECTED_MANIFEST_SHA256,
        "repair manifest bytes differ from the editor-approved contract",
    )

    _expect(manifest.get("schema_version") == 1, "schema_version must be 1")
    _expect(
        manifest.get("issue") == "https://github.com/DataTalksClub/content/issues/2",
        "issue URL differs",
    )
    baseline = _mapping(manifest, "baseline")
    _expect(baseline.get("commit") == BASELINE_COMMIT, "baseline commit differs")
    _expect(
        baseline.get("legacy_commit") == LEGACY_COMMIT,
        "legacy generator commit differs",
    )
    _expect(
        baseline.get("migration_manifest_sha256") == MIGRATION_MANIFEST_SHA256,
        "migration manifest digest differs",
    )
    _expect(
        sha256_file(root / "migration.yaml") == MIGRATION_MANIFEST_SHA256,
        "migration.yaml is not byte-identical to the baseline",
    )
    _expect(manifest.get("expected_delta") == EXPECTED_DELTA, "expected delta differs")
    _expect(manifest.get("current_counts") == EXPECTED_COUNTS, "current counts differ")
    _expect(manifest.get("invariants") == EXPECTED_INVARIANTS, "invariants differ")
    _validate_generation_contract(_mapping(manifest, "generation"))

    repairs = manifest.get("repairs")
    _expect(isinstance(repairs, list), "repairs must be a list")
    _expect(len(repairs) == len(EXPECTED_REPAIRS), "repair row count differs")
    result_paths: set[str] = set()
    added_paths: set[str] = set()

    for ordinal, (row, expected) in enumerate(zip(repairs, EXPECTED_REPAIRS, strict=True), start=1):
        _expect(isinstance(row, dict), f"repair {ordinal}: row must be a mapping")
        prefix = f"repair {ordinal}"
        _expect(
            _canonical_digest(row) == expected["row_digest"],
            f"{prefix}: provenance differs from the pinned repair plan",
        )
        _expect(row.get("ordinal") == ordinal, f"{prefix}: ordinal differs")
        for key in ("record", "baseline_blob", "action"):
            _expect(row.get(key) == expected[key], f"{prefix}: {key} differs")
        _expect(HEX_40.fullmatch(str(row.get("baseline_blob"))), f"{prefix}: invalid blob")
        _expect(
            HEX_64.fullmatch(str(row.get("baseline_sha256"))),
            f"{prefix}: invalid baseline SHA-256",
        )
        record_path = root / str(row["record"])
        _expect(record_path.is_file(), f"{prefix}: record does not exist")

        result = _mapping(row, "result", prefix)
        result_path = result.get("path")
        _expect(result_path == expected["result"], f"{prefix}: result path differs")
        _expect(result.get("added") is expected["added"], f"{prefix}: added flag differs")
        _expect(
            result.get("sha256") == expected["result_sha256"],
            f"{prefix}: result differs from the editor-approved digest",
        )
        _expect(result_path not in result_paths, f"{prefix}: duplicate result path")
        result_paths.add(str(result_path))
        if result["added"]:
            added_paths.add(str(result_path))
        _validate_result(root, result, prefix)

        action = row["action"]
        if action == "correct_image_path":
            for key in ("old_value", "new_value"):
                _expect(row.get(key) == expected[key], f"{prefix}: {key} differs")
            _expect(row.get("field") == "image", f"{prefix}: corrected field differs")
            metadata = load_article_front_matter(record_path)
            _expect(
                metadata.get("image") == expected["new_value"],
                f"{prefix}: corrected image value differs",
            )
        else:
            metadata = (
                load_article_front_matter(record_path)
                if str(row["record"]).startswith("articles/")
                else load_yaml_mapping(record_path)
            )
            _expect(
                metadata.get("image") == result_path,
                f"{prefix}: declared image does not match result",
            )

        override = expected.get("preview_title_override")
        _expect(
            row.get("preview_title_override") == override,
            f"{prefix}: preview title override differs",
        )
        if override is not None:
            _expect(
                HEX_64.fullmatch(str(row.get("preview_input_sha256"))),
                f"{prefix}: preview input SHA-256 is invalid",
            )
        if action in GENERATED_ACTIONS:
            _validate_generated_row(row, result, prefix)
        elif action == "restore_identical":
            _expect(
                result.get("sha256")
                == "9961d52e08c39164dc4da47062597a87e15551bc45b43183017d8e4eccfc158f",
                f"{prefix}: historical restoration digest differs",
            )

    _expect(len(added_paths) == 8, "added repair asset count differs")
    _validate_repository_counts(root)
    return {
        "repairs": len(repairs),
        "added_media": len(added_paths),
        "media": EXPECTED_COUNTS["media"],
        "manifest_sha256": sha256_file(path),
    }


def _validate_generation_contract(generation: dict[str, Any]) -> None:
    _expect(
        _canonical_digest(generation) == EXPECTED_GENERATION_DIGEST,
        "generation provenance differs from the pinned contract",
    )
    _expect(generation.get("source_commit") == LEGACY_COMMIT, "generation source differs")
    _expect(generation.get("viewport") == {"width": 940, "height": 550}, "viewport differs")
    _expect(generation.get("jpeg_quality") == 85, "JPEG quality differs")
    shared = _mapping(generation, "shared_inputs", "generation")
    renderers = _mapping(generation, "renderers", "generation")
    toolchain = _mapping(generation, "toolchain", "generation")
    external = _mapping(generation, "external_resources", "generation")
    for name in ("styles", "package", "lock"):
        item = _mapping(shared, name, "generation shared input")
        _expect(HEX_40.fullmatch(str(item.get("blob"))), f"{name} blob is invalid")
        _expect(HEX_64.fullmatch(str(item.get("sha256"))), f"{name} digest is invalid")
    for name in ("post", "book", "podcast"):
        item = _mapping(renderers, name, "generation renderer")
        for key in ("wrapper_blob", "renderer_blob", "template_blob"):
            _expect(HEX_40.fullmatch(str(item.get(key))), f"{name} {key} is invalid")
        for key in ("wrapper_sha256", "renderer_sha256", "template_sha256"):
            _expect(HEX_64.fullmatch(str(item.get(key))), f"{name} {key} is invalid")
    _expect(toolchain.get("puppeteer") == "3.3.0", "Puppeteer version differs")
    chromium = _mapping(toolchain, "chromium", "generation toolchain")
    _expect(
        HEX_64.fullmatch(str(chromium.get("executable_sha256"))),
        "Chromium executable digest is invalid",
    )
    _expect(external.get("alegreya_sans") == "loaded", "preview font was not loaded")
    _expect(external.get("remote_images") == "none requested", "remote image input detected")


def _validate_generated_row(
    row: dict[str, Any],
    result: dict[str, Any],
    prefix: str,
) -> None:
    _expect(isinstance(row.get("command"), str), f"{prefix}: command is missing")
    inputs = _mapping(row, "generator_inputs", prefix)
    for key, value in inputs.items():
        if key.endswith("_blob"):
            _expect(HEX_40.fullmatch(str(value)), f"{prefix}: {key} is invalid")
        if key.endswith("_sha256"):
            _expect(HEX_64.fullmatch(str(value)), f"{prefix}: {key} is invalid")
    approval = _mapping(row, "editor_approval", prefix)
    _expect(approval.get("status") == "FINAL", f"{prefix}: editor approval is not final")
    _expect(approval.get("verdict") == "APPROVE", f"{prefix}: editor rejected output")
    _expect(
        approval.get("comment_url") == EDITOR_COMMENT_URL,
        f"{prefix}: editor approval URL differs",
    )
    _expect(approval.get("approver") == EDITOR_APPROVER, f"{prefix}: approver differs")
    _expect(
        approval.get("approved_at") == EDITOR_APPROVED_AT,
        f"{prefix}: approval time differs",
    )
    try:
        datetime.fromisoformat(str(approval["approved_at"]).replace("Z", "+00:00"))
    except (KeyError, ValueError) as error:
        raise RepairManifestError(f"{prefix}: approval time is invalid") from error
    _expect(
        approval.get("output_sha256") == result.get("sha256"),
        f"{prefix}: approved output digest differs",
    )


def _validate_result(root: Path, result: dict[str, Any], prefix: str) -> None:
    relative = str(result.get("path", ""))
    _expect(relative and not relative.startswith("/"), f"{prefix}: unsafe result path")
    _expect(
        "\\" not in relative and ".." not in relative.split("/"), f"{prefix}: unsafe result path"
    )
    path = root.joinpath(*relative.split("/"))
    current = root
    try:
        for part in relative.split("/"):
            current = current / part
            metadata = current.lstat()
            _expect(not stat.S_ISLNK(metadata.st_mode), f"{prefix}: result is a symlink")
    except FileNotFoundError as error:
        raise RepairManifestError(f"{prefix}: result file is missing") from error
    _expect(stat.S_ISREG(metadata.st_mode), f"{prefix}: result is not a regular file")
    extension = path.suffix
    _expect(extension in ALLOWED_MEDIA_EXTENSIONS, f"{prefix}: result extension is invalid")
    media = path.read_bytes()
    _expect(_media_signature_error(extension, media) is None, f"{prefix}: media signature differs")
    _expect(result.get("bytes") == len(media), f"{prefix}: result byte count differs")
    _expect(
        result.get("sha256") == hashlib.sha256(media).hexdigest(),
        f"{prefix}: result digest differs",
    )
    width, height = media_dimensions(extension, media)
    _expect(result.get("width") == width, f"{prefix}: result width differs")
    _expect(result.get("height") == height, f"{prefix}: result height differs")
    expected_type = "image/svg+xml" if extension == ".svg" else f"image/{extension.lstrip('.')}"
    if extension in {".jpg", ".jpeg"}:
        expected_type = "image/jpeg"
    _expect(result.get("media_type") == expected_type, f"{prefix}: media type differs")
    _expect(HEX_64.fullmatch(str(result.get("sha256"))), f"{prefix}: result digest is invalid")


def media_dimensions(extension: str, media: bytes) -> tuple[int, int]:
    if extension == ".png":
        return struct.unpack(">II", media[16:24])
    if extension == ".gif":
        return struct.unpack("<HH", media[6:10])
    if extension in {".jpg", ".jpeg"}:
        index = 2
        while index + 9 <= len(media):
            if media[index] != 0xFF:
                index += 1
                continue
            marker = media[index + 1]
            index += 2
            if marker in {0xD8, 0xD9}:
                continue
            if marker == 0xDA:
                break
            if index + 2 > len(media):
                break
            length = int.from_bytes(media[index : index + 2], "big")
            if length < 2 or index + length > len(media):
                break
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
                height = int.from_bytes(media[index + 3 : index + 5], "big")
                width = int.from_bytes(media[index + 5 : index + 7], "big")
                return width, height
            index += length
    raise RepairManifestError("repair result dimensions are unreadable")


def _validate_repository_counts(root: Path) -> None:
    actual = {
        "articles": len(list((root / "articles").glob("*.md"))),
        "podcasts": len(list((root / "podcasts").glob("*.yaml"))),
        "podcast_transcripts": len(list((root / "podcasts/transcripts").glob("*.yaml"))),
        "books": len(list((root / "books").glob("*.yaml"))),
        "media": sum(
            1
            for category in ("posts", "podcast", "books")
            for path in (root / "images" / category).rglob("*")
            if path.is_file() and not path.is_symlink()
        ),
    }
    _expect(actual == EXPECTED_COUNTS, "repository counts differ from repair manifest")


def _mapping(value: dict[str, Any], key: str, prefix: str = "manifest") -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise RepairManifestError(f"{prefix}: {key} must be a mapping")
    return result


def _canonical_digest(value: Any) -> str:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    except (TypeError, ValueError) as error:
        raise RepairManifestError("repair provenance contains unsupported values") from error
    return hashlib.sha256(rendered).hexdigest()


def _expect(condition: object, message: str) -> None:
    if not condition:
        raise RepairManifestError(message)


def emit_attestation(root: Path, commit_sha: str) -> dict[str, Any]:
    if not HEX_40.fullmatch(commit_sha):
        raise RepairManifestError("replacement commit must be a lowercase 40-character SHA")
    summary = validate_repair_manifest(root)
    return {
        "schema_version": 1,
        "repository": "https://github.com/DataTalksClub/content",
        "replacement_commit": commit_sha,
        "baseline_commit": BASELINE_COMMIT,
        "repair_manifest": MANIFEST_RELATIVE_PATH.as_posix(),
        "repair_manifest_sha256": summary["manifest_sha256"],
        "counts": EXPECTED_COUNTS,
        "editor_approval": EDITOR_COMMENT_URL,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate missing-media repair provenance")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--attest-commit")
    parser.add_argument("--attestation-output", type=Path)
    args = parser.parse_args()
    try:
        if args.attest_commit:
            attestation = emit_attestation(args.root.resolve(), args.attest_commit)
            rendered = json.dumps(attestation, indent=2, sort_keys=True) + "\n"
            if args.attestation_output:
                args.attestation_output.parent.mkdir(parents=True, exist_ok=True)
                args.attestation_output.write_text(rendered, encoding="utf-8")
            else:
                print(rendered, end="")
            return 0
        summary = validate_repair_manifest(args.root.resolve())
    except (OSError, RepairManifestError) as error:
        print(f"STOP: {error}")
        return 1
    print(
        "PASS: "
        f"repairs={summary['repairs']}, "
        f"added_media={summary['added_media']}, "
        f"media={summary['media']}, "
        f"manifest_sha256={summary['manifest_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
