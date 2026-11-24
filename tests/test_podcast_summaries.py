from __future__ import annotations

import pytest
import yaml

from scripts.podcast_summaries import (
    SummaryError,
    check_summary,
    load_episodes,
    transcript_text,
    write_summary,
)

GOOD = "First paragraph.\n\nSecond, with open-source tools.\n\nThird and last."


def test_check_summary_normalizes_wrapped_paragraphs() -> None:
    assert check_summary("First\nparagraph.\n\n\nSecond.\n\nThird.\n") == (
        "First paragraph.\n\nSecond.\n\nThird."
    )


@pytest.mark.parametrize(
    "text",
    [
        "One.\n\nTwo.",
        "One — two.\n\nThree.\n\nFour.",
        "One – two.\n\nThree.\n\nFour.",
        "One - two.\n\nThree.\n\nFour.",
        "## Heading\n\nTwo.\n\nThree.",
        "- bullet\n\nTwo.\n\nThree.",
    ],
)
def test_check_summary_rejects_style_breaks(text: str) -> None:
    with pytest.raises(SummaryError):
        check_summary(text)


def test_write_summary_appends_and_replaces_without_touching_other_fields() -> None:
    source = "slug: x\ntitle: 'A: title'\nnotes: 'keep me'\n"
    written = write_summary(source, check_summary(GOOD))
    assert written.startswith(source)
    assert yaml.safe_load(written)["summary"] == GOOD

    replaced = write_summary(
        written + "image: x.jpg\n", check_summary(GOOD.replace("Third", "3rd"))
    )
    loaded = yaml.safe_load(replaced)
    assert loaded["summary"] == GOOD.replace("Third", "3rd")
    assert loaded["image"] == "x.jpg"
    assert replaced.count("summary:") == 1


def test_long_paragraphs_wrap_for_review_and_round_trip() -> None:
    paragraph = " ".join(["word"] * 60)
    summary = f"{paragraph}\n\n{paragraph}\n\n{paragraph}"
    written = write_summary("slug: x\n", summary)
    assert max(len(line) for line in written.splitlines()) <= 100
    loaded = yaml.safe_load(written)["summary"]
    assert [" ".join(block.split()) for block in loaded.split("\n\n")] == summary.split("\n\n")


def test_real_episodes_load_newest_first_with_readable_transcripts() -> None:
    episodes = load_episodes()
    assert episodes
    keys = [(episode.season, episode.episode) for episode in episodes]
    assert keys == sorted(keys, reverse=True)
    text = transcript_text(episodes[0])
    assert text.count("\n") > 10
