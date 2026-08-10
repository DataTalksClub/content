# DataTalks.Club content

This repository is the editorial source for DataTalks.Club articles, podcast
episodes, podcast transcripts, and books.

## Layout

```text
articles/                 Markdown articles with YAML front matter
podcasts/                 One YAML metadata file per podcast episode
podcasts/transcripts/     One separate YAML transcript per podcast episode
books/                    One YAML file per book
editorial-overlays/       Strict manifests for post-migration editorial fields
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
description: A practical discussion of data engineering roles, skills, and career development.
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
uv run python -m scripts.repair_manifest
uv run python -m scripts.editorial_overlay
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Every podcast must provide `description` as a non-empty string scalar. The
validator rejects missing, blank, null, numeric, boolean, sequence, and mapping
descriptions. It also rejects embedded podcast transcript arrays, missing or
orphaned transcript files, malformed front matter/YAML, duplicate slugs and
legacy paths, and unsupported content file types. It resolves every article
front-matter image, local Markdown/HTML body image, podcast image, and book
cover/preview.

Local media references may use `images/...` or `/images/...`. They must resolve
to a regular, non-symlink file below the matching `images/posts`,
`images/podcast`, or `images/books` root. Only lowercase GIF, JPEG, PNG, and safe
SVG files are accepted. Validation fails on missing media, traversal or encoded
traversal, filesystem paths, ambiguous query/fragment spellings, backslashes,
wrong roots, unsupported/double extensions, mismatched signatures, unsafe SVG,
non-regular files, and files over 10 MiB. HTTP(S) body images remain external;
required metadata images must always be repository media. The validator never
fetches remote images or substitutes a fallback.

## Migration provenance

`migration.yaml` records the exact source repository revision and migrated item
counts. `scripts/migrate_legacy_content.py` documents the deterministic legacy
conversion. It excludes legacy `_template.md` files, copies article Markdown
and media bytes unchanged, and separates podcast transcript data without
rewriting transcript segments.

The immutable migration contains 55 articles, 205 podcasts, 203 transcripts, 98
books, and 807 copied media files. The checked
`repairs/2026-08-09-missing-media.yaml` composes a post-migration overlay: eight
allowlisted media additions and two article `image` scalar corrections, for a
current media count of 815. It binds the exact baseline, source/generator inputs,
toolchain, output hashes, and the SHA-bound DTC editor approval. Changing any
approved output invalidates that approval and requires a new issue comment and
manifest update before commit.

`editorial-overlays/2026-08-10-podcast-descriptions.yaml` is a separate
post-migration editorial overlay for
[content issue 3](https://github.com/DataTalksClub/content/issues/3). It permits
only the `description` key on its exact 19 podcast paths. The manifest pins the
immutable legacy source revision, migration manifest, baseline content commit,
target set, description digests, complete target-file digests, and its own
contract digest in the validator. Missing or extra rows, duplicate or
noncanonical paths, wrong keys or types, digest drift, target-file drift, and
undeclared fields fail closed.

Source verification composes the overlays without weakening the migration
boundary. For a declared podcast, it validates the editorial manifest, removes
only the exact declared `description` from the candidate mapping, and then
compares every remaining field with the metadata deterministically reconstructed
from the immutable legacy checkout. The SHA-bound missing-media repair remains
unchanged and scoped to its own declared article and media outputs.

For generated previews, an identified DTC editor opens every candidate at its
original resolution and records `APPROVE` or `REJECT` for each exact output path
and SHA-256 in the issue. The editor checks the record identity and DTC design,
the intended author/guest/cover, text fit, and resource/layout integrity. Only
the per-path hashes explicitly approved in that issue comment may be recorded as
final in the repair manifest.

When the pinned legacy checkout is available locally, verify the migration
against it byte-for-byte and field-for-field:

```bash
uv run python -m scripts.verify_migration ../datatalksclub.github.io
```

The source checkout must be detached at the revision recorded in
`migration.yaml`. Verification proves all 807 baseline media bytes, all
unaffected content, the exact eight additions, and only the two declared scalar
changes. Run all local checks with:

```bash
make check
make verify-source SOURCE=../datatalksclub.github.io
```

CI repeats those checks against the pinned public legacy checkout and publishes
a deterministic JSON replacement attestation. To reproduce it locally for an
exact 40-character replacement commit, write it only below the ignored `.tmp/`
directory:

```bash
make attest \
  COMMIT=0123456789abcdef0123456789abcdef01234567 \
  OUTPUT=.tmp/attestation/missing-media-repair.json
```
