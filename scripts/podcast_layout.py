from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

SEASON_DIRECTORY_RE = re.compile(r"s(?P<season>[0-9]{2})$")
EPISODE_FILENAME_RE = re.compile(
    r"e(?P<episode>[0-9]{2})(?P<collision>-[a-z0-9][a-z0-9.-]*)?\.yaml$"
)
TRANSCRIPT_FILENAME_SUFFIX = "-transcript.yaml"
LEGACY_TRANSCRIPTS_DIRECTORY = "transcripts"


@dataclass(frozen=True)
class PodcastIdentity:
    slug: str
    season: int
    episode: int


@dataclass(frozen=True)
class PodcastPaths:
    episode: Path
    transcript: Path


def seasonal_podcast_paths(identities: Iterable[PodcastIdentity]) -> dict[str, PodcastPaths]:
    """Return stable seasonal paths for a set of podcast identities.

    The normal path is ``sNN/eMM.yaml``. A duplicate season/episode pair keeps
    the first slug-sorted record at that path; later records get a
    slug-qualified filename. The same episode stem is used for its sibling
    transcript, so every mapping is deterministic without changing metadata.
    """

    grouped: dict[tuple[int, int], list[PodcastIdentity]] = defaultdict(list)
    seen_slugs: set[str] = set()
    for identity in identities:
        if identity.slug in seen_slugs:
            raise ValueError(f"duplicate podcast slug: {identity.slug}")
        seen_slugs.add(identity.slug)
        _validate_identity_number(identity.season, "season", identity.slug)
        _validate_identity_number(identity.episode, "episode", identity.slug)
        if not identity.slug or Path(identity.slug).name != identity.slug:
            raise ValueError(f"podcast slug is not a filename-safe value: {identity.slug!r}")
        grouped[(identity.season, identity.episode)].append(identity)

    paths: dict[str, PodcastPaths] = {}
    for (season, episode), group in sorted(grouped.items()):
        for ordinal, identity in enumerate(sorted(group, key=lambda item: item.slug)):
            stem = f"e{episode:02d}"
            if ordinal:
                stem = f"{stem}-{identity.slug}"
            episode_path = Path(f"s{season:02d}") / f"{stem}.yaml"
            transcript_path = episode_path.with_name(
                f"{episode_path.stem}{TRANSCRIPT_FILENAME_SUFFIX}"
            )
            paths[identity.slug] = PodcastPaths(episode_path, transcript_path)
    return paths


def parse_seasonal_episode_path(path: Path, podcasts_dir: Path) -> tuple[int, int, str] | None:
    """Parse a seasonal episode path relative to ``podcasts_dir``.

    The returned tuple contains season, episode, and an optional collision
    suffix. Transcript siblings are deliberately excluded.
    """

    try:
        relative = path.relative_to(podcasts_dir)
    except ValueError:
        return None
    if len(relative.parts) != 2:
        return None
    season_match = SEASON_DIRECTORY_RE.fullmatch(relative.parts[0])
    if season_match is None or relative.name.endswith(TRANSCRIPT_FILENAME_SUFFIX):
        return None
    episode_match = EPISODE_FILENAME_RE.fullmatch(relative.name)
    if episode_match is None:
        return None
    return (
        int(season_match.group("season")),
        int(episode_match.group("episode")),
        episode_match.group("collision") or "",
    )


def is_seasonal_transcript_path(path: Path, podcasts_dir: Path) -> bool:
    try:
        relative = path.relative_to(podcasts_dir)
    except ValueError:
        return False
    if len(relative.parts) != 2 or SEASON_DIRECTORY_RE.fullmatch(relative.parts[0]) is None:
        return False
    return relative.name.endswith(TRANSCRIPT_FILENAME_SUFFIX) and relative.suffix == ".yaml"


def discover_episode_paths(podcasts_dir: Path) -> list[Path]:
    """Discover seasonal episodes and legacy flat episodes.

    Legacy flat files remain readable so older checkouts and migration
    fixtures can still be imported. The current repository contains no flat
    episode files.
    """

    if not podcasts_dir.is_dir():
        return []
    paths = [path for path in podcasts_dir.glob("*.yaml") if path.is_file()]
    for season_dir in sorted(podcasts_dir.iterdir()):
        if not season_dir.is_dir() or SEASON_DIRECTORY_RE.fullmatch(season_dir.name) is None:
            continue
        paths.extend(
            path
            for path in season_dir.glob("*.yaml")
            if path.is_file() and parse_seasonal_episode_path(path, podcasts_dir) is not None
        )
    return sorted(paths)


def discover_transcript_paths(podcasts_dir: Path) -> list[Path]:
    """Discover seasonal sibling transcripts and legacy transcript files."""

    if not podcasts_dir.is_dir():
        return []
    paths = []
    legacy_dir = podcasts_dir / LEGACY_TRANSCRIPTS_DIRECTORY
    if legacy_dir.is_dir():
        paths.extend(path for path in legacy_dir.glob("*.yaml") if path.is_file())
    for season_dir in sorted(podcasts_dir.iterdir()):
        if not season_dir.is_dir() or SEASON_DIRECTORY_RE.fullmatch(season_dir.name) is None:
            continue
        paths.extend(
            path
            for path in season_dir.glob(f"*{TRANSCRIPT_FILENAME_SUFFIX}")
            if path.is_file() and is_seasonal_transcript_path(path, podcasts_dir)
        )
    return sorted(paths)


def _validate_identity_number(value: int, field: str, slug: str) -> None:
    if type(value) is not int or not 0 < value < 100:
        raise ValueError(f"podcast {slug!r} has invalid {field}: {value!r}")
