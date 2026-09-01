from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from scripts.podcast_layout import discover_episode_paths
from scripts.podcast_platform import (
    CANONICAL_SPOTIFY_CREATORS_EPISODE_PREFIX,
    canonicalize_podcast_platform_links,
    is_legacy_anchor_url,
)
from scripts.validate_content import ContentError, validate_repository

ROOT = Path(__file__).resolve().parents[1]


def test_canonicalization_preserves_episode_id_and_ids_anchor() -> None:
    metadata = {
        "ids": {"anchor": "AB-Testing---Jakob-Graff-e1eq73v"},
        "links": {
            "anchor": ("https://anchor.fm/datatalksclub/episodes/AB-Testing---Jakob-Graff-e1eq73v")
        },
    }

    assert canonicalize_podcast_platform_links(metadata) is True
    assert metadata["links"]["anchor"] == (
        CANONICAL_SPOTIFY_CREATORS_EPISODE_PREFIX + "AB-Testing---Jakob-Graff-e1eq73v"
    )
    assert metadata["ids"]["anchor"] == "AB-Testing---Jakob-Graff-e1eq73v"


def test_current_podcast_sources_have_no_legacy_anchor_urls() -> None:
    episodes = [
        yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in discover_episode_paths(ROOT / "podcasts")
    ]

    assert not any(
        is_legacy_anchor_url((episode.get("links") or {}).get("anchor")) for episode in episodes
    )

    example = next(
        episode
        for episode in episodes
        if episode.get("slug") == "ab-testing-and-product-experimentation"
    )
    assert example["links"]["anchor"] == (
        CANONICAL_SPOTIFY_CREATORS_EPISODE_PREFIX + "AB-Testing---Jakob-Graff-e1eq73v"
    )
    assert example["ids"]["anchor"] == "AB-Testing---Jakob-Graff-e1eq73v"


def test_validator_rejects_legacy_anchor_url(tmp_path: Path) -> None:
    for relative in (
        "articles",
        "podcasts",
        "books",
        "images/posts",
        "images/podcast",
        "images/books",
    ):
        (tmp_path / relative).mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "images/podcast/data-team-roles.jpg",
        tmp_path / "images/podcast/episode.jpg",
    )
    (tmp_path / "podcasts/episode.yaml").write_text(
        "\n".join(
            (
                "slug: episode",
                "legacy_path: /podcast/episode.html",
                "title: Episode",
                "season: 1",
                "episode: 1",
                "guests: []",
                "image: images/podcast/episode.jpg",
                "description: Episode description",
                "links:",
                "  anchor: https://anchor.fm/datatalksclub/episodes/example-e1",
                "",
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(ContentError, match="canonical Spotify for Creators URL"):
        validate_repository(tmp_path)
