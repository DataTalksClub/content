from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from scripts import sync_podcast_audio as audio


def _episode(path, *, tokens=(), titles=(), guests=(), day=None, audio_url=None):
    return {
        "path": Path(path),
        "tokens": set(tokens),
        "titles": {audio._normal(title) for title in titles},
        "guests": set(guests),
        "date": day,
        "audio_url": audio_url,
        "duration_seconds": None,
    }


def _item(title, *, token=None, day=date(2026, 1, 1)):
    return {
        "title": title,
        "titles": {audio._normal(title), audio._normal(title.rsplit(" - ", 1)[0])},
        "guest": audio._normal(title.rsplit(" - ", 1)[1]).replace(" ", "")
        if " - " in title
        else "",
        "date": day,
        "token": token,
        "audio_url": f"https://anchor.fm/s/x/podcast/play/{token or title}",
        "duration_seconds": 60,
    }


def test_token_from_creator_url_and_id():
    assert (
        audio._token(
            "https://creators.spotify.com/pod/profile/x/episodes/Some-Title-e3ib29q/a-ack1822"
        )
        == "e3ib29q"
    )
    assert (
        audio._token(
            "https://podcasters.spotify.com/pod/show/x/episodes/Some-Title---Guest-e3s7e78"
        )
        == "e3s7e78"
    )
    assert audio._token("Some-Title-e1snqcb") == "e1snqcb"


def test_seconds():
    assert audio._seconds("01:03:22") == 3802
    assert audio._seconds("42:05") == 2525
    assert audio._seconds(None) is None


def test_matching_rules_and_shared_tokens():
    by_token = _episode("a.yaml", tokens={"e1aaaaa"}, titles={"Anything"})
    # Two files that carry one token (a copy-paste slip) fall through to the
    # date rules: one by title, the other by guest.
    shared_title = _episode(
        "b.yaml", tokens={"e2bbbbb"}, titles={"Doing Research"}, day=date(2023, 1, 14)
    )
    shared_guest = _episode(
        "c.yaml",
        tokens={"e2bbbbb"},
        titles={"Retitled"},
        guests={"paulineclavelloux"},
        day=date(2023, 1, 21),
    )
    undated = _episode("d.yaml", titles={"Building an AI Platform: Memory and Tools"})
    items = [
        _item("Old - Someone", token="e1aaaaa"),
        _item("Doing Research - Johanna Bayer", token="e2bbbbb", day=date(2023, 1, 13)),
        _item("Indie Hacking - Pauline Clavelloux", day=date(2023, 1, 20)),
        _item("AI Platform: Memory and Tools - Dewang Sultania", token="e9zzzzz"),
        _item("Conference Interviews"),
    ]
    matched, unmatched = audio.match(items, [by_token, shared_title, shared_guest, undated])
    assert matched[Path("a.yaml")]["title"] == "Old - Someone"
    assert matched[Path("b.yaml")]["title"].startswith("Doing Research")
    assert matched[Path("c.yaml")]["title"].startswith("Indie Hacking")
    assert matched[Path("d.yaml")]["title"].startswith("AI Platform")
    assert [item["title"] for item in unmatched] == ["Conference Interviews"]


def test_write_places_fields_after_links(tmp_path):
    path = tmp_path / "e01.yaml"
    path.write_text("slug: x\nlinks:\n  youtube: https://y\nseason: 1\n")
    assert audio.write(path, "https://anchor.fm/a.mp3", 61)
    assert path.read_text() == (
        "slug: x\nlinks:\n  youtube: https://y\naudio_url: https://anchor.fm/a.mp3\n"
        "duration_seconds: 61\nseason: 1\n"
    )
    assert not audio.write(path, "https://anchor.fm/a.mp3", 61)
    assert yaml.safe_load(path.read_text())["duration_seconds"] == 61


def test_feed_is_configured():
    assert audio.configured_feed().startswith("https://anchor.fm/")
