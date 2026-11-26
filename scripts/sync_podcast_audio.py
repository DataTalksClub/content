"""Record each episode's audio file from the podcast RSS feed.

Run it whenever a new episode is published.  The feed (``rss_feed`` in
``podcast-platforms.yaml``) lists every published episode with an
``<enclosure>`` audio URL and an ``<itunes:duration>``.  This script matches
each feed item to an episode file under ``podcasts/`` and, for an episode that
has no ``audio_url`` yet, writes two fields after its ``links:`` block:

    audio_url: https://anchor.fm/s/41286f68/podcast/play/...
    duration_seconds: 3802

Matching, strongest first:

1. the Spotify for Creators episode token (``...-e3ib29q``), which the feed's
   ``<link>`` and the episode's ``links.anchor`` / ``links.spotify_for_creators``
   (or ``ids.anchor``) both end with;
2. otherwise the normalised title (the feed's "Title - Guest" against the
   episode's ``title`` and ``short``) on a publish date within three days of
   ``dateadded``;
3. otherwise the feed's guest (the people slug spelling of "- Guest Name")
   on that same date window, for an episode retitled on the site;
4. otherwise, for an episode without a date, the title alone when exactly one
   episode carries it (or ends with it).

A token two episode files share proves nothing and falls through to 2-4.

Feed items that match no episode, and episodes still without audio, are
printed.  An episode that already has ``audio_url`` is never touched, so the
script is safe to run again.

    uv run python scripts/sync_podcast_audio.py            # fetch the feed and write
    uv run python scripts/sync_podcast_audio.py --dry-run  # report only
    uv run python scripts/sync_podcast_audio.py --feed saved-feed.xml
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import yaml

ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
ROOT = Path(__file__).resolve().parents[1]
SHOW_SETTINGS = ROOT / "podcast-platforms.yaml"
EPISODE_FILE = re.compile(r"^e\d+\.yaml$")
TOKEN = re.compile(r"-(e[0-9a-z]{5,8})(?:/[^/]*)?/?$")
DATE_SLACK_DAYS = 3


def _token(url: str | None) -> str | None:
    if not url:
        return None
    match = TOKEN.search(url.split("?", 1)[0])
    return match.group(1) if match else None


def _normal(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _seconds(raw: str | None) -> int | None:
    if not raw:
        return None
    parts = [int(part) for part in raw.strip().split(":")]
    total = 0
    for part in parts:
        total = total * 60 + part
    return total


def configured_feed() -> str:
    feed = (yaml.safe_load(SHOW_SETTINGS.read_text()) or {}).get("rss_feed")
    if not isinstance(feed, str) or not feed.startswith("https://"):
        raise SystemExit(f"{SHOW_SETTINGS.name}: rss_feed must be an https URL")
    return feed


def feed_items(source: str) -> list[dict]:
    if source.startswith("https://"):
        request = urllib.request.Request(source, headers={"User-Agent": "dtc-content-audio/1"})
        with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
            body = response.read()
    else:
        body = Path(source).read_bytes()
    items = []
    for item in ET.fromstring(body).iter("item"):
        enclosure = item.find("enclosure")
        if enclosure is None or not enclosure.get("url", "").startswith("https://"):
            continue
        title = item.findtext("title") or ""
        items.append(
            {
                "title": title,
                "titles": {_normal(title), _normal(title.rsplit(" - ", 1)[0])},
                # "Title - Guest Name": the guest as the people slug spells it.
                "guest": _normal(title.rsplit(" - ", 1)[1]).replace(" ", "")
                if " - " in title
                else "",
                "date": parsedate_to_datetime(item.findtext("pubDate")).date(),
                "token": _token(item.findtext("link")),
                "audio_url": enclosure.get("url"),
                "duration_seconds": _seconds(item.findtext(f"{ITUNES}duration")),
            }
        )
    return items


def episodes() -> list[dict]:
    found = []
    for path in sorted((ROOT / "podcasts").glob("s*/e*.yaml")):
        if not EPISODE_FILE.match(path.name):
            continue
        record = yaml.safe_load(path.read_text())
        links = record.get("links") or {}
        ids = record.get("ids") or {}
        tokens = {
            _token(value)
            for value in (links.get("anchor"), links.get("spotify_for_creators"), ids.get("anchor"))
            if isinstance(value, str)
        } - {None}
        added = record.get("dateadded")
        if isinstance(added, str):
            added = datetime.strptime(added, "%Y-%m-%d").date()
        found.append(
            {
                "path": path,
                "tokens": tokens,
                "titles": {_normal(str(record.get(key) or "")) for key in ("title", "short")}
                - {""},
                "guests": set(record.get("guests") or ()),
                "date": added if isinstance(added, date) else None,
                "audio_url": record.get("audio_url"),
                "duration_seconds": record.get("duration_seconds"),
            }
        )
    return found


def match(items: list[dict], episodes: list[dict]) -> tuple[dict, list[dict]]:
    # A token two episode files share (a copy-paste slip in the source) proves
    # nothing, so those episodes fall through to the title rules.
    owners: dict[str, list[dict]] = {}
    for episode in episodes:
        for token in episode["tokens"]:
            owners.setdefault(token, []).append(episode)
    by_token = {token: found[0] for token, found in owners.items() if len(found) == 1}
    matched: dict[Path, dict] = {}
    unmatched = []
    for item in items:
        episode = by_token.get(item["token"]) if item["token"] else None
        if episode is None:
            candidates = [
                episode
                for episode in episodes
                if episode["titles"] & item["titles"]
                and episode["date"] is not None
                and abs((episode["date"] - item["date"]).days) <= DATE_SLACK_DAYS
            ]
            if not candidates and item["guest"]:
                # A retitled episode: its guest on the same date.
                candidates = [
                    episode
                    for episode in episodes
                    if item["guest"] in episode["guests"]
                    and episode["date"] is not None
                    and abs((episode["date"] - item["date"]).days) <= DATE_SLACK_DAYS
                ]
            if not candidates:
                # An episode filed without a date: the title alone, when
                # exactly one episode carries it or ends with it.
                candidates = [
                    episode
                    for episode in episodes
                    if episode["date"] is None
                    and any(
                        own == title or (len(title) > 20 and own.endswith(title))
                        for own in episode["titles"]
                        for title in item["titles"]
                    )
                ]
            episode = candidates[0] if len(candidates) == 1 else None
        if episode is None or episode["path"] in matched:
            unmatched.append(item)
            continue
        matched[episode["path"]] = item
    return matched, unmatched


def write(path: Path, audio_url: str, duration_seconds: int | None) -> bool:
    """Put the two fields after the ``links:`` block."""

    lines = [
        line
        for line in path.read_text().splitlines()
        if not line.startswith(("audio_url:", "duration_seconds:"))
    ]
    fields = [f"audio_url: {audio_url}"]
    if duration_seconds:
        fields.append(f"duration_seconds: {duration_seconds}")
    try:
        at = lines.index("links:") + 1
        while at < len(lines) and lines[at].startswith((" ", "-")):
            at += 1
    except ValueError:
        at = len(lines)
    updated = "\n".join(lines[:at] + fields + lines[at:]) + "\n"
    if updated == path.read_text():
        return False
    path.write_text(updated)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--feed", help="a saved feed file or URL (default: rss_feed)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    items = feed_items(args.feed or configured_feed())
    known = episodes()
    matched, unmatched = match(items, known)
    by_path = {episode["path"]: episode for episode in known}
    changed = 0
    for path, item in sorted(matched.items()):
        if by_path[path]["audio_url"]:
            continue
        if not args.dry_run and write(path, item["audio_url"], item["duration_seconds"]):
            changed += 1
        print(f"{'would add' if args.dry_run else 'added'} audio: {path.relative_to(ROOT)}")
    print(
        f"feed items: {len(items)}; episodes: {len(known)}; "
        f"matched: {len(matched)}; written: {changed}"
    )
    for item in unmatched:
        print(f"unmatched feed item: {item['date']} {item['title']}")
    for episode in known:
        if episode["path"] not in matched and not episode["audio_url"]:
            print(f"episode without audio: {episode['path'].relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
