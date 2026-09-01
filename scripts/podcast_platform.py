"""Compatibility-preserving podcast platform URL canonicalization."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

LEGACY_ANCHOR_HOSTS = frozenset({"anchor.fm", "www.anchor.fm"})
LEGACY_ANCHOR_EPISODE_PREFIX = "https://anchor.fm/datatalksclub/episodes/"
CANONICAL_SPOTIFY_CREATORS_EPISODE_PREFIX = (
    "https://creators.spotify.com/pod/profile/datatalksclub/episodes/"
)


def is_legacy_anchor_url(value: Any) -> bool:
    """Return whether a value is an old Anchor-host URL."""

    if not isinstance(value, str):
        return False
    return urlsplit(value).hostname in LEGACY_ANCHOR_HOSTS


def canonicalize_podcast_platform_links(metadata: dict[str, Any]) -> bool:
    """Canonicalize a legacy DTC Anchor episode URL in-place.

    The source schema keeps ``links.anchor`` as the importer-compatible field
    name. ``ids.anchor`` is an opaque, stable provider episode identifier and
    is deliberately not renamed or rewritten.
    """

    links = metadata.get("links")
    if not isinstance(links, dict):
        return False
    value = links.get("anchor")
    if not isinstance(value, str) or not value.startswith(LEGACY_ANCHOR_EPISODE_PREFIX):
        return False
    links["anchor"] = CANONICAL_SPOTIFY_CREATORS_EPISODE_PREFIX + value.removeprefix(
        LEGACY_ANCHOR_EPISODE_PREFIX
    )
    return True
