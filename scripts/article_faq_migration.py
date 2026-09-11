"""Pull legacy article FAQ pairs from datatalksclub.github.io into article frontmatter.

Some blog articles carry a ``{% include faq-accordion.html
faqs=site.data.faqs.<key> %}`` marker in their body. The question/answer pairs
never lived in the article Markdown on the legacy Jekyll site -- they lived in
``_data/faqs/<key>.yml`` in ``DataTalksClub/datatalksclub.github.io``.
`DataTalksClub/dtc-website`'s ``scripts/build_public_projection.py`` expects
those pairs to travel with the article itself, as a frontmatter ``faq:`` list
(see its ``_article_faq_record()``); an article with the accordion marker and
no frontmatter ``faq:`` fails that build.

The first ten articles got this frontmatter by hand, once, in commit
8be8587c ("Move legacy article FAQ pairs into article frontmatter"). This
script is the reusable, repeatable replacement: given a checkout of the
legacy site pinned to some revision, it finds every article with the
accordion marker, reads the matching ``_data/faqs/<key>.yml`` -- the marker's
``key`` names the file, and is *not* always the article's own slug; the
2020-12-23 Slack-communities article's key is
``data-science-slack-communities``, for instance -- and writes a ``faq:``
block into that article's frontmatter, in the exact shape
`build_public_projection.py` and `content/article_faq_format.py` (both in
dtc-website) already validate: a list of ``{question, answer}`` mappings,
values stripped of surrounding whitespace, no extra keys.

Default mode is a dry-run report: every article with the marker, and what the
script would do to it (write / already correct / conflict) and why. Nothing
is written to disk unless ``--apply`` is passed.

A CONFLICT is an article that already carries a frontmatter ``faq:`` whose
content differs from what the legacy source has *now* -- for example because
of a later, deliberate editorial correction made directly in `content` (the
2025-09-23 ai-dev-tools-zoomcamp article's answers were hand-edited to point
at the "AI Shipping Blog" after the Substack -> AI Shipping Blog rename; the
legacy site's data file was never updated to match). The script never
overwrites an existing ``faq:`` block -- a conflict is reported and left for a
human to resolve, even with ``--apply``.

Run it from a clean, pinned legacy checkout::

    uv run python -m scripts.article_faq_migration \\
        --legacy-root <datatalksclub.github.io@pinned> \\
        [--legacy-revision <rev>] [--apply]

Nothing here is invented: a marker with no matching data file, an empty data
file, or a data file whose entries don't fit the question/answer shape is a
hard failure, never a rendered guess.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

# The broad shape scripts/build_public_projection.py itself uses to spot a FAQ
# accordion include in an article body -- kept in lockstep with that regex so
# this script never silently walks past a marker shape the build would still
# treat as a FAQ accordion.
FAQ_INCLUDE_BROAD = re.compile(r"^\{%\s*include\s+faq-accordion\.html[^%]*%\}$")
# The one legacy include shape the migration actually knows how to resolve: it
# names a `_data/faqs/<key>.yml` file in the legacy site repository.
FAQ_INCLUDE = re.compile(
    r"^\{%\s*include\s+faq-accordion\.html\s+faqs=site\.data\.faqs\.(?P<key>[a-z0-9-]+)\s*%\}$"
)

LEGACY_FAQ_REPOSITORY = "https://github.com/DataTalksClub/datatalksclub.github.io"
LEGACY_FAQ_DIRECTORY = "_data/faqs"
#: The revision dtc-website's scripts/build_public_projection.py pins as
#: LEGACY_MAIN_REVISION (equivalently, the retired content/article_faq.py's
#: LEGACY_FAQ_REVISION) at the time this script was written. Override with
#: --legacy-revision to read a newer legacy commit as more FAQ data files land
#: there ahead of their article migrating into this repository.
DEFAULT_LEGACY_REVISION = "ee43d3fa0929faf691178d79f19528e6f15a83e5"

#: The same bounds dtc-website's content/article_faq_format.py enforces on a
#: frontmatter faq pair, so a pair that would be rejected at ingest is
#: rejected here instead, at the source.
QUESTION_MAX_CHARACTERS = 500
ANSWER_MAX_CHARACTERS = 5_000
#: Wide enough that no question or answer within the bound above ever wraps --
#: PyYAML's plain/quoted scalar folding at a narrower width would change the
#: block's bytes and make an already-correct article look like a conflict.
DUMP_WIDTH = ANSWER_MAX_CHARACTERS + 1_000


class ArticleFaqMigrationError(ValueError):
    """One article FAQ migration input is missing, ambiguous, or unusable."""


@dataclass
class ArticlePlan:
    path: Path
    key: str
    status: str  # "write" | "unchanged" | "conflict"
    pairs: list[dict[str, str]] = field(default_factory=list)
    detail: str = ""


def _run(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise ArticleFaqMigrationError((result.stderr or result.stdout).strip() or " ".join(args))
    return result.stdout


def _normalize_repository(url: str) -> str:
    url = url.strip()
    if url.endswith(".git"):
        url = url[: -len(".git")]
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url[len("git@github.com:") :]
    return url.rstrip("/").lower()


def verify_legacy_root(legacy_root: Path, revision: str) -> None:
    if not (legacy_root / ".git").exists():
        raise ArticleFaqMigrationError(f"--legacy-root is not a git checkout: {legacy_root}")
    origin = _run(["git", "remote", "get-url", "origin"], cwd=legacy_root)
    if _normalize_repository(origin) != _normalize_repository(LEGACY_FAQ_REPOSITORY):
        raise ArticleFaqMigrationError(f"--legacy-root origin is not {LEGACY_FAQ_REPOSITORY}")
    _run(["git", "cat-file", "-e", revision + "^{commit}"], cwd=legacy_root)


def legacy_faq_pairs(legacy_root: Path, revision: str, key: str) -> list[dict[str, str]]:
    """Return one legacy FAQ data file as verbatim, stripped question/answer pairs."""

    source_path = f"{LEGACY_FAQ_DIRECTORY}/{key}.yml"
    result = subprocess.run(
        ["git", "show", f"{revision}:{source_path}"],
        cwd=legacy_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ArticleFaqMigrationError(f"legacy FAQ source missing: {source_path} @ {revision}")
    try:
        parsed = yaml.safe_load(result.stdout)
    except yaml.YAMLError as error:
        raise ArticleFaqMigrationError(
            f"legacy FAQ source is invalid YAML: {source_path}"
        ) from error
    if not isinstance(parsed, list) or not parsed:
        raise ArticleFaqMigrationError(f"legacy FAQ source is not a non-empty list: {source_path}")
    pairs: list[dict[str, str]] = []
    for entry in parsed:
        if not isinstance(entry, dict) or set(entry) != {"question", "answer"}:
            raise ArticleFaqMigrationError(f"legacy FAQ entry shape rejected: {source_path}")
        question = str(entry["question"]).strip()
        answer = str(entry["answer"]).strip()
        if not question or len(question) > QUESTION_MAX_CHARACTERS:
            raise ArticleFaqMigrationError(f"legacy FAQ question rejected: {source_path}")
        if not answer or len(answer) > ANSWER_MAX_CHARACTERS:
            raise ArticleFaqMigrationError(f"legacy FAQ answer rejected: {source_path}")
        pairs.append({"question": question, "answer": answer})
    return pairs


def read_article(path: Path) -> tuple[str, dict[str, Any], str, int]:
    """Return (full_text, metadata, body, closing-delimiter line index).

    The closing-delimiter index is where a new frontmatter key is inserted --
    directly in front of the closing ``---`` line, exactly as commit 8be8587c
    did it by hand.
    """

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ArticleFaqMigrationError(f"missing front matter: {path.name}")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ArticleFaqMigrationError(f"unterminated front matter: {path.name}") from error
    metadata = yaml.safe_load("\n".join(lines[1:end])) or {}
    if not isinstance(metadata, dict):
        raise ArticleFaqMigrationError(f"front matter is not a mapping: {path.name}")
    body = "\n".join(lines[end + 1 :])
    return text, metadata, body, end


def faq_marker(body: str) -> tuple[str, int] | None:
    """Return (legacy data key, body line index) for the article's FAQ accordion, if any."""

    lines = body.splitlines()
    broad_hits = [
        index for index, line in enumerate(lines) if FAQ_INCLUDE_BROAD.match(line.strip())
    ]
    if not broad_hits:
        return None
    if len(broad_hits) > 1:
        raise ArticleFaqMigrationError("article carries more than one FAQ accordion include")
    strict_hits = [
        (match.group("key"), index)
        for index, line in enumerate(lines)
        if (match := FAQ_INCLUDE.match(line.strip()))
    ]
    if not strict_hits or strict_hits[0][1] != broad_hits[0]:
        raise ArticleFaqMigrationError(
            "FAQ accordion include has an unrecognized shape (expected `faqs=site.data.faqs.<key>`)"
        )
    return strict_hits[0]


def normalize_existing(value: Any) -> list[dict[str, str]] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        raise ArticleFaqMigrationError("existing frontmatter faq is not a non-empty list")
    normalized: list[dict[str, str]] = []
    for entry in value:
        if not isinstance(entry, dict) or not {"question", "answer"} <= set(entry):
            raise ArticleFaqMigrationError("existing frontmatter faq entry shape unexpected")
        normalized.append(
            {"question": str(entry["question"]).strip(), "answer": str(entry["answer"]).strip()}
        )
    return normalized


def render_faq_block(pairs: list[dict[str, str]]) -> str:
    """Render a frontmatter ``faq:`` block exactly as commit 8be8587c did it.

    Verified byte-for-byte against nine of the ten precedent articles (the
    tenth, ai-dev-tools-zoomcamp, has since been hand-corrected in content and
    is intentionally left alone -- see the module docstring).
    """

    return yaml.safe_dump({"faq": pairs}, allow_unicode=True, sort_keys=False, width=DUMP_WIDTH)


def apply_faq_block(text: str, end: int, pairs: list[dict[str, str]]) -> str:
    lines = text.splitlines(keepends=True)
    block = render_faq_block(pairs)
    if not block.endswith("\n"):
        block += "\n"
    insertion = block + "\n"  # blank line before the closing delimiter, matching precedent
    return "".join(lines[:end] + [insertion] + lines[end:])


def plan_articles(content_root: Path, legacy_root: Path, revision: str) -> list[ArticlePlan]:
    plans: list[ArticlePlan] = []
    used_keys: dict[str, Path] = {}
    for path in sorted((content_root / "articles").rglob("*.md")):
        _, metadata, body, _ = read_article(path)
        marker = faq_marker(body)
        if marker is None:
            continue
        key, _ = marker
        if key in used_keys:
            raise ArticleFaqMigrationError(
                f"two articles claim the same FAQ key {key!r}: "
                f"{used_keys[key].relative_to(content_root)} and {path.relative_to(content_root)}"
            )
        used_keys[key] = path

        pairs = legacy_faq_pairs(legacy_root, revision, key)
        existing = normalize_existing(metadata.get("faq"))
        if existing is None:
            plans.append(ArticlePlan(path=path, key=key, status="write", pairs=pairs))
        elif existing == pairs:
            plans.append(ArticlePlan(path=path, key=key, status="unchanged", pairs=pairs))
        else:
            differing = sum(1 for a, b in zip(existing, pairs, strict=False) if a != b)
            differing += abs(len(existing) - len(pairs))
            detail = (
                f"{len(existing)} existing pair(s) vs {len(pairs)} from the legacy source "
                f"now; {differing} differ"
            )
            plans.append(
                ArticlePlan(path=path, key=key, status="conflict", pairs=pairs, detail=detail)
            )
    return plans


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--legacy-revision", default=DEFAULT_LEGACY_REVISION)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the planned faq: blocks. Default is a dry-run report only.",
    )
    args = parser.parse_args()

    content_root = args.content_root.resolve()
    legacy_root = args.legacy_root.resolve()

    try:
        verify_legacy_root(legacy_root, args.legacy_revision)
        plans = plan_articles(content_root, legacy_root, args.legacy_revision)
    except ArticleFaqMigrationError as error:
        print(f"STOP: {error}")
        return 1

    if not plans:
        print("PASS: no article carries a faq-accordion include")
        return 0

    for plan in plans:
        relative = plan.path.relative_to(content_root)
        if plan.status == "write":
            print(f"WRITE    {relative}  (key={plan.key}, {len(plan.pairs)} pairs)")
        elif plan.status == "unchanged":
            print(f"OK       {relative}  (key={plan.key}) already matches the legacy source")
        else:
            print(
                f"CONFLICT {relative}  (key={plan.key}) {plan.detail}"
                " -- left untouched, resolve by hand"
            )

    writes = [plan for plan in plans if plan.status == "write"]
    unchanged = [plan for plan in plans if plan.status == "unchanged"]
    conflicts = [plan for plan in plans if plan.status == "conflict"]

    if args.apply:
        for plan in writes:
            text, _, _, end = read_article(plan.path)
            updated = apply_faq_block(text, end, plan.pairs)
            plan.path.write_text(updated, encoding="utf-8")
        print(
            f"APPLIED: wrote faq: to {len(writes)} article(s); "
            f"{len(unchanged)} already correct; {len(conflicts)} conflict(s) left untouched"
        )
    else:
        print(
            f"DRY RUN: {len(writes)} to write, {len(unchanged)} already correct, "
            f"{len(conflicts)} conflict(s) (never auto-applied). Re-run with --apply to write."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
