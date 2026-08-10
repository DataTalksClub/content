from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from scripts.validate_content import ContentError, validate_repository

ROOT = Path(__file__).resolve().parents[1]


def _build_minimal_repository(
    tmp_path: Path,
    description_lines: tuple[str, ...],
) -> Path:
    for relative in (
        "articles",
        "podcasts/transcripts",
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
                *description_lines,
                "",
            )
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_repository_content_is_valid() -> None:
    counts = validate_repository(ROOT)

    assert counts == {
        "articles": 55,
        "podcasts": 205,
        "transcripts": 203,
        "books": 98,
        "media": 815,
        "referenced_media": 761,
    }


def test_podcast_transcripts_are_separate_yaml_documents() -> None:
    for podcast_path in sorted((ROOT / "podcasts").glob("*.yaml")):
        podcast = yaml.safe_load(podcast_path.read_text(encoding="utf-8"))
        transcript_reference = podcast.get("transcript")
        assert not isinstance(transcript_reference, list)
        if transcript_reference is None:
            continue

        transcript_path = ROOT / "podcasts" / transcript_reference
        transcript = yaml.safe_load(transcript_path.read_text(encoding="utf-8"))
        assert transcript["podcast"] == podcast["slug"]
        assert isinstance(transcript["segments"], list)


def test_validator_rejects_embedded_transcript(tmp_path: Path) -> None:
    (tmp_path / "articles").mkdir()
    (tmp_path / "podcasts" / "transcripts").mkdir(parents=True)
    (tmp_path / "books").mkdir()
    (tmp_path / "podcasts" / "episode.yaml").write_text(
        "\n".join(
            (
                "slug: episode",
                "legacy_path: /podcast/episode.html",
                "title: Episode",
                "season: 1",
                "episode: 1",
                "guests: []",
                "description: Episode description",
                "transcript: []",
                "",
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(ContentError, match="transcript must be stored in a separate YAML file"):
        validate_repository(tmp_path)


@pytest.mark.parametrize(
    "description_lines",
    (
        pytest.param((), id="missing"),
        pytest.param(("description: '   '",), id="blank"),
        pytest.param(("description:",), id="null"),
        pytest.param(("description: 42",), id="numeric"),
        pytest.param(("description: true",), id="boolean"),
        pytest.param(("description: []",), id="sequence"),
        pytest.param(("description: {summary: Details}",), id="mapping"),
    ),
)
def test_validator_rejects_invalid_podcast_description(
    tmp_path: Path,
    description_lines: tuple[str, ...],
) -> None:
    root = _build_minimal_repository(tmp_path, description_lines)

    with pytest.raises(
        ContentError,
        match="podcasts/episode.yaml: description must be a non-empty string",
    ):
        validate_repository(root)
