"""Draft each podcast episode's ``summary:`` from its transcript with Claude.

The summary is the episode's longer description: three to six plain paragraphs
on what the conversation covered and its main takeaways. It is written into
the episode YAML itself, so every summary is reviewed in git like the rest of
the episode copy, and the website syncs it from here like any other field.

Usage (see ``make podcast-summaries``)::

    uv run --with anthropic python -m scripts.podcast_summaries --latest 5
    uv run --with anthropic python -m scripts.podcast_summaries --episode s25/e09 --force
    uv run --with anthropic python -m scripts.podcast_summaries --all

Episodes that already carry a summary are skipped unless ``--force`` is given.

Credentials: the Anthropic SDK resolves them itself (``ANTHROPIC_API_KEY``,
``ANTHROPIC_AUTH_TOKEN`` or an ``ant auth login`` profile). Without any of
those, ``--backend claude-cli`` runs the same prompt through the locally
signed-in ``claude`` command instead; ``auto`` (the default) picks whichever
is available.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PODCASTS_ROOT = REPOSITORY_ROOT / "podcasts"
MODEL = "claude-opus-5-5"
SUMMARY_WIDTH = 100
#: Some slack above the prompt's 550-word target before a draft is refused.
MAX_WORDS = 650

SYSTEM_PROMPT = """\
You write the summary that appears on a DataTalks.Club podcast episode page, \
above the timestamps and the full transcript. Readers use it to decide whether \
the episode is worth their time and to recall what was said.

Write three to six paragraphs of plain prose, 300 to 550 words in total, \
each paragraph three to six sentences. Pick the threads that matter most \
rather than retelling every exchange:
- Open with who the guest is (as they describe themselves in the conversation) \
and what the episode is about.
- Then follow the conversation's main threads in order: what was discussed, \
the concrete examples, tools, numbers and opinions the guest gave.
- Close with a paragraph on the key takeaways a practitioner can act on, \
written as prose, not a list.

Rules:
- Use only what is said in the transcript. Do not add facts, titles, \
companies, numbers or links that the transcript does not contain.
- Plain and factual. No hype, no marketing language, no rhetorical questions, \
no "in this episode you will learn".
- Refer to the host as Alexey and to the guest by first name after the first \
mention.
- Never use dashes as punctuation: no em dashes, no en dashes, no spaced \
hyphens. Use commas, periods, colons or parentheses instead. Hyphens inside \
compound words (open-source, real-time) are fine.
- No headings, bullet points, bold text or Markdown. Separate paragraphs with \
one blank line.
- Output only the summary text."""

#: Dashes used as punctuation: em dash, en dash, or a hyphen with a space on
#: either side. A hyphen inside a word ("open-source") is not punctuation.
PUNCTUATION_DASH_RE = re.compile(r"[—–]|\s-\s|\s--?\s")
MARKDOWN_RE = re.compile(r"^\s*(#|[-*] |\d+\. )|\*\*", re.MULTILINE)
TOP_LEVEL_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*:", re.MULTILINE)


class SummaryError(RuntimeError):
    """A drafted summary broke the style rules or the model declined."""


@dataclass(frozen=True)
class EpisodeFile:
    path: Path
    season: int
    episode: int
    record: dict

    @property
    def label(self) -> str:
        return f"s{self.season:02d}/e{self.episode:02d}"


def load_episodes(root: Path = PODCASTS_ROOT) -> list[EpisodeFile]:
    """Every episode file with a transcript, newest first."""

    episodes = []
    for path in sorted(root.glob("s[0-9][0-9]/e*.yaml")):
        if path.name.endswith("-transcript.yaml"):
            continue
        record = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or not record.get("transcript"):
            continue
        episodes.append(EpisodeFile(path, record["season"], record["episode"], record))
    episodes.sort(key=lambda item: (item.season, item.episode), reverse=True)
    return episodes


def transcript_text(episode: EpisodeFile) -> str:
    """The transcript as the model reads it: chapter headers and speaker lines."""

    transcript_path = episode.path.parent / episode.record["transcript"]
    transcript = yaml.safe_load(transcript_path.read_text(encoding="utf-8"))
    lines = []
    for segment in transcript["segments"]:
        if segment.get("header"):
            lines.append(f"\n## {segment['header']}")
        elif segment.get("line"):
            speaker = segment.get("who") or "Speaker"
            lines.append(f"{speaker}: {segment['line']}")
    return "\n".join(lines).strip()


def user_prompt(episode: EpisodeFile) -> str:
    record = episode.record
    return (
        f"Episode title: {record['title']}\n"
        f"Short description: {record.get('description', '')}\n\n"
        f"<transcript>\n{transcript_text(episode)}\n</transcript>\n\n"
        "Write the summary."
    )


def check_summary(text: str) -> str:
    """Normalize paragraphs and refuse text that breaks the style rules."""

    paragraphs = [" ".join(block.split()) for block in re.split(r"\n\s*\n", text.strip())]
    paragraphs = [paragraph for paragraph in paragraphs if paragraph]
    problems = []
    if not 3 <= len(paragraphs) <= 6:
        problems.append(f"expected 3 to 6 paragraphs, got {len(paragraphs)}")
    joined = "\n\n".join(paragraphs)
    words = len(joined.split())
    if words > MAX_WORDS:
        problems.append(f"{words} words, the limit is {MAX_WORDS}")
    if PUNCTUATION_DASH_RE.search(joined):
        problems.append("uses a dash as punctuation")
    if MARKDOWN_RE.search(text):
        problems.append("contains Markdown formatting")
    if problems:
        raise SummaryError("; ".join(problems))
    return joined


def summary_block(summary: str) -> str:
    """The ``summary:`` YAML block, wrapped for review, paragraphs kept apart."""

    wrapped = [
        textwrap.fill(paragraph, width=SUMMARY_WIDTH - 2, break_on_hyphens=False)
        for paragraph in summary.split("\n\n")
    ]
    body = "\n\n".join(wrapped)
    indented = "\n".join(f"  {line}" if line else "" for line in body.splitlines())
    return f"summary: |-\n{indented}\n"


def write_summary(source: str, summary: str) -> str:
    """Return the episode YAML with its summary set, everything else untouched."""

    block = summary_block(summary)
    match = re.search(r"^summary:", source, re.MULTILINE)
    if match is None:
        return source.rstrip("\n") + "\n" + block
    following = TOP_LEVEL_KEY_RE.search(source, match.end())
    end = following.start() if following else len(source)
    return source[: match.start()] + block + source[end:]


def _draft_with_api(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()
    if message.stop_reason == "refusal":
        raise SummaryError("the model declined to summarize this transcript")
    return "".join(block.text for block in message.content if block.type == "text")


def _draft_with_claude_cli(prompt: str) -> str:
    result = subprocess.run(
        [
            "claude",
            "-p",
            "--model",
            MODEL,
            "--effort",
            "high",
            "--system-prompt",
            SYSTEM_PROMPT,
            "--tools",
            "",
            "--no-session-persistence",
            "--output-format",
            "text",
        ],
        input=prompt,
        capture_output=True,
        text=True,
        check=False,
        timeout=900,
    )
    if result.returncode != 0:
        raise SummaryError(f"claude exited with {result.returncode}: {result.stderr.strip()}")
    return result.stdout


def pick_backend(choice: str) -> str:
    if choice != "auto":
        return choice
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return "api"
    if shutil.which("claude"):
        return "claude-cli"
    return "api"


def draft_summary(episode: EpisodeFile, backend: str, attempts: int = 2) -> str:
    draft = _draft_with_api if backend == "api" else _draft_with_claude_cli
    prompt = user_prompt(episode)
    last_error: SummaryError | None = None
    for _ in range(attempts):
        try:
            return check_summary(draft(prompt))
        except SummaryError as error:
            last_error = error
            prompt = (
                f"{user_prompt(episode)}\n\nA previous draft was rejected: {error}. "
                "Follow every rule this time."
            )
    raise SummaryError(f"{episode.label}: {last_error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--latest", type=int, metavar="N", help="the N newest episodes")
    selection.add_argument(
        "--episode", action="append", metavar="sNN/eNN", help="one episode (repeatable)"
    )
    selection.add_argument("--all", action="store_true", help="every episode with a transcript")
    parser.add_argument("--force", action="store_true", help="replace existing summaries")
    parser.add_argument("--dry-run", action="store_true", help="print, do not write")
    parser.add_argument("--backend", choices=("auto", "api", "claude-cli"), default="auto")
    args = parser.parse_args(argv)

    episodes = load_episodes()
    if args.latest:
        episodes = episodes[: args.latest]
    elif args.episode:
        wanted = set(args.episode)
        episodes = [episode for episode in episodes if episode.label in wanted]
        missing = wanted - {episode.label for episode in episodes}
        if missing:
            parser.error(f"no episode with a transcript: {', '.join(sorted(missing))}")
    if not args.force:
        episodes = [episode for episode in episodes if not episode.record.get("summary")]

    backend = pick_backend(args.backend)
    failures = 0
    for episode in episodes:
        try:
            summary = draft_summary(episode, backend)
        except SummaryError as error:
            failures += 1
            print(f"FAILED {error}", file=sys.stderr)
            continue
        if args.dry_run:
            print(f"== {episode.label} {episode.record['title']}\n\n{summary}\n")
            continue
        source = episode.path.read_text(encoding="utf-8")
        episode.path.write_text(write_summary(source, summary), encoding="utf-8")
        print(f"wrote {episode.path.relative_to(REPOSITORY_ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
