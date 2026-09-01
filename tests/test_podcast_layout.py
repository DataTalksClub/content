from __future__ import annotations

from pathlib import Path

import pytest

from scripts.podcast_layout import (
    PodcastIdentity,
    discover_episode_paths,
    discover_transcript_paths,
    seasonal_podcast_paths,
)


def test_seasonal_paths_use_zero_padded_siblings() -> None:
    paths = seasonal_podcast_paths((PodcastIdentity("episode", 2, 10),))

    assert paths["episode"].episode == Path("s02/e10.yaml")
    assert paths["episode"].transcript == Path("s02/e10-transcript.yaml")


def test_duplicate_episode_numbers_get_stable_slug_qualified_paths() -> None:
    paths = seasonal_podcast_paths(
        (
            PodcastIdentity("zulu", 3, 4),
            PodcastIdentity("alpha", 3, 4),
        )
    )

    assert paths["alpha"].episode == Path("s03/e04.yaml")
    assert paths["alpha"].transcript == Path("s03/e04-transcript.yaml")
    assert paths["zulu"].episode == Path("s03/e04-zulu.yaml")
    assert paths["zulu"].transcript == Path("s03/e04-zulu-transcript.yaml")


@pytest.mark.parametrize(
    "identity",
    (
        PodcastIdentity("episode", 0, 1),
        PodcastIdentity("episode", 100, 1),
        PodcastIdentity("episode", 1, 0),
        PodcastIdentity("episode", 1, 100),
    ),
)
def test_seasonal_paths_reject_numbers_outside_two_digits(identity: PodcastIdentity) -> None:
    with pytest.raises(ValueError, match="invalid"):
        seasonal_podcast_paths((identity,))


def test_discovery_distinguishes_episode_and_transcript_siblings(tmp_path: Path) -> None:
    podcasts_dir = tmp_path / "podcasts"
    season_dir = podcasts_dir / "s02"
    season_dir.mkdir(parents=True)
    (season_dir / "e10.yaml").write_text("{}\n", encoding="utf-8")
    (season_dir / "e10-transcript.yaml").write_text("{}\n", encoding="utf-8")

    assert discover_episode_paths(podcasts_dir) == [season_dir / "e10.yaml"]
    assert discover_transcript_paths(podcasts_dir) == [season_dir / "e10-transcript.yaml"]
