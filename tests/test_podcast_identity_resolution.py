"""Source identity regression for the five previously broken legacy redirects."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_season_three_publisher_identities_are_unique():
    records = [
        yaml.safe_load(p.read_text())
        for p in (ROOT / "podcasts/s03").glob("*.yaml")
        if not p.name.endswith("-transcript.yaml")
    ]
    identities = [(r["season"], r["episode"]) for r in records]
    assert len(identities) == len(set(identities))
    by_video = {r["ids"]["youtube"]: r for r in records}
    assert by_video["AYi7b-8GPm4"]["episode"] == 5
    assert by_video["gqroEsTyLD0"]["episode"] == 4


def test_restored_episodes_keep_distinct_platform_and_transcript_identity():
    for episode, video in [(7, "T1R-IfYrRFY"), (8, "xC5lqvfSfLU"), (9, "oWVmQDqZ7tw")]:
        path = ROOT / f"podcasts/s25/e{episode:02d}.yaml"
        record = yaml.safe_load(path.read_text())
        assert (record["season"], record["episode"]) == (25, episode)
        assert record["ids"]["youtube"] == video
        transcript = yaml.safe_load((path.parent / record["transcript"]).read_text())
        assert transcript["podcast"] == record["slug"]
        assert transcript["segments"]
        assert (ROOT / record["image"]).is_file()
