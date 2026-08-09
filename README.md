# DataTalks.Club content

This repository is the editorial source for DataTalks.Club articles, podcast
episodes, podcast transcripts, and books.

## Layout

```text
articles/                 Markdown articles with YAML front matter
podcasts/                 One YAML metadata file per podcast episode
podcasts/transcripts/     One separate YAML transcript per podcast episode
books/                    One YAML file per book
images/posts/             Article images at their legacy paths
images/podcast/           Podcast images at their legacy paths
images/books/             Book images at their legacy paths
```

Articles remain Markdown because their bodies are long-form editorial content.
Podcast and book records are YAML because their content is structured. Podcast
transcripts are deliberately not embedded in episode metadata: the episode file
contains a relative `transcript` reference to a separate YAML document.

Filenames and `legacy_path` values are compatibility identifiers. Do not rename
them as part of an editorial change; the website uses them to preserve existing
public URLs and search-engine indexing.

## Podcast example

```yaml
slug: data-engineering-career
legacy_path: /podcast/data-engineering-career.html
title: Data Engineering Career
season: 1
episode: 1
guests:
  - person-short-id
transcript: transcripts/data-engineering-career.yaml
```

The matching transcript uses this shape:

```yaml
podcast: data-engineering-career
segments:
  - header: Introductions
  - who: Alexey
    time: "0:12"
    sec: 12
    line: Welcome to the show.
```

## Books and articles

Book files are YAML mappings. Existing discussion archives remain structured
lists in the book record, while the former prose body is stored as `summary`.

Article files keep their original Markdown body and YAML front matter verbatim.
This avoids a lossy conversion of authored prose and preserves the legacy
filename used to derive the public article URL.

## Validation

Use [uv](https://docs.astral.sh/uv/) for all repository tooling:

```bash
uv sync --frozen
uv run python scripts/validate_content.py
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

The validator rejects embedded podcast transcript arrays, missing or orphaned
transcript files, malformed front matter/YAML, duplicate slugs and legacy paths,
and unsupported content file types.

## Migration provenance

`migration.yaml` records the exact source repository revision and migrated item
counts. `scripts/migrate_legacy_content.py` documents the deterministic legacy
conversion. It excludes legacy `_template.md` files, copies article Markdown
and media bytes unchanged, and separates podcast transcript data without
rewriting transcript segments.

When the pinned legacy checkout is available locally, verify the migration
against it byte-for-byte and field-for-field:

```bash
uv run python -m scripts.verify_migration ../datatalksclub.github.io
```
