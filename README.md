# DataTalks.Club content

This repository is the editorial source for DataTalks.Club articles, podcast
episodes, podcast transcripts, and books.

## Layout

```text
articles/yyyy/            Dated Markdown articles with YAML front matter
podcasts/sNN/eMM.yaml     One YAML metadata file per podcast episode
podcasts/sNN/eMM-transcript.yaml
                          Optional transcript sibling for that episode
books/yyyy/               Dated YAML record per book
migration/                Immutable migration and post-migration manifests
migration/editorial-overlays/
                          Strict manifests for post-migration editorial fields
migration/repairs/        Strict manifests for post-migration repairs
migration/podcast-removals.yaml
                          Explicit podcast removal manifest
images/posts/             Article images at their legacy paths
images/podcast/           Podcast images at their legacy paths
images/books/             Book images at their legacy paths
```

Articles remain Markdown because their bodies are long-form editorial content.
Podcast and book records are YAML because their content is structured. Podcast
transcripts are deliberately not embedded in episode metadata: the episode file
contains a relative `transcript` reference to a separate YAML document.

The `slug` and `legacy_path` values are compatibility identifiers. The website
uses them to preserve existing public URLs and search-engine indexing, so they
remain unchanged when an episode moves within this source tree. The seasonal
filename is an organization-level identifier and is derived from the episode's
numeric `season` and `episode` fields.

Articles use `articles/yyyy/yy-mm-dd-slug.md`, with the date taken from the
`datepublished` front-matter field. Books use the analogous
`books/yyyy/yy-mm-dd-slug.yaml` layout, with the date taken from `start`.
Missing or unusable dates are validation errors; dates are never guessed from
the current date. These physical paths organize source records only: canonical
slugs, `legacy_path` routes, links, image references, and source provenance
remain unchanged.

Podcast platform links
----------------------

`links.anchor` remains the importer-compatible source key, but current DTC
episode URLs use `https://creators.spotify.com/pod/profile/datatalksclub/episodes/`.
The episode path and ID after `/episodes/` are preserved exactly. `ids.anchor`
remains the stable opaque provider episode identifier and is not renamed or
rewritten. Legacy `anchor.fm` episode URLs are canonicalized when the importer
reconstructs expected podcast metadata, while validation rejects them in current
podcast front matter. Anchor references in non-podcast authored content are
outside this migration and remain unchanged.

Podcast audio
-------------

Each episode carries its audio file and length from the show's RSS feed
(`rss_feed` in `podcast-platforms.yaml`):

```yaml
audio_url: https://anchor.fm/s/41286f68/podcast/play/...
duration_seconds: 3900
```

The website plays `audio_url` in its own player. **When a new episode is
published**, run

```sh
uv run python scripts/sync_podcast_audio.py
```

and commit the episode files it changed. It matches feed items to episodes by
the Spotify for Creators episode token in `links.anchor`, then by title and
date, then by guest and date; it only fills episodes that have no `audio_url`
yet, so it is safe to run again. It prints the feed items it could not match
(conference specials and minis that are not episodes on the site) and any
episode still without audio. `--dry-run` reports without writing.

## Podcast example

```yaml
slug: data-engineering-career
legacy_path: /podcast/data-engineering-career.html
title: Data Engineering Career
description: A practical discussion of data engineering roles, skills, and career development.
season: 2
episode: 10
guests:
  - person-short-id
transcript: e10-transcript.yaml
```

The example episode lives at `podcasts/s02/e10.yaml`; its matching sibling
transcript lives at `podcasts/s02/e10-transcript.yaml` and uses this shape:

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
The dated directory and filename are an organization-level index; they do not
rewrite article front matter or canonical route/source references.
This avoids a lossy conversion of authored prose and preserves the legacy
filename used to derive the public article URL.

### Article picture: first image, or `cover:`

An article's picture (its thumbnail in the blog list and on the home page, and
its link preview) is chosen like a Substack post's:

- By default it is the **first image in the body** that the site publishes, a
  Markdown `![alt](/images/posts/...)` or an HTML `<img src="/images/posts/...">`.
  Screenshots and diagrams count too. A remote (`https://`) image is never
  published, so it is skipped. The website sets a wide or tall picture whole on a
  soft background in the square thumbnail, never cropping it.
- `cover: images/posts/<folder>/<file>` picks a different image instead, for
  example a course illustration. It is optional and must name a file in this
  repository.
- Only an article with **no image at all** carries a generated card:
  `preview: images/posts/<folder>/preview.png` (banner-generator `dtc-article`:
  the title, author and date), with its 1200x630 social card beside it as
  `preview-og.png`. The website refuses a `preview:` on an article that has a
  cover or a body image, so the card is never kept by hand next to a real picture.

`image:` is the article's legacy cover from the old site and is not the picture.

## Validation

Use [uv](https://docs.astral.sh/uv/) for all repository tooling:

```bash
uv sync --frozen
uv run python scripts/validate_content.py
uv run python -m scripts.removal_manifest
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

Podcast loaders accept the former flat `podcasts/*.yaml` plus
`podcasts/transcripts/*.yaml` layout for older source checkouts. New records must
use the seasonal layout and keep the transcript reference as the exact sibling
filename `<episode-stem>-transcript.yaml`. No duplicate or symlink aliases are
kept in the current tree. Season 3 episode identities follow the publisher RSS: Lior Barak is S03E04
and Oleg Novikov is S03E05. See `migration/podcast-identity-resolution.md`
for the evidence and reversible correction.

## Migration provenance

`migration/migration.yaml` records the exact source repository revision and migrated item
counts. `scripts/migrate_legacy_content.py` documents the deterministic legacy
conversion. It excludes legacy `_template.md` files, copies article Markdown
and media bytes unchanged, and separates podcast transcript data without
rewriting transcript segments. Its podcast output uses the seasonal layout;
episode metadata is preserved apart from canonicalizing legacy DTC Anchor episode
URLs and the local sibling transcript reference.

The immutable migration contains 55 articles, 205 podcasts, 203 transcripts, 98
books, and 807 copied media files. The checked
`migration/repairs/2026-08-09-missing-media.yaml` composes a post-migration overlay: eight
allowlisted media additions and two article `image` scalar corrections, for a
current media count of 815. It binds the exact baseline, source/generator inputs,
toolchain, output hashes, and the SHA-bound DTC editor approval. Changing any
approved output invalidates that approval and requires a new issue comment and
manifest update before commit.

`migration/editorial-overlays/2026-08-10-podcast-descriptions.yaml` is a separate
post-migration editorial overlay for
[content issue 3](https://github.com/DataTalksClub/content/issues/3). It permits
only the `description` key on its exact 18 podcast paths. The manifest pins the
immutable legacy source revision, migration manifest, baseline content commit,
target set, description digests, complete target-file digests, and its own
contract digest in the validator. Missing or extra rows, duplicate or
noncanonical paths, wrong keys or types, digest drift, target-file drift, and
undeclared fields fail closed.

`migration/podcast-removals.yaml` records the two explicitly removed legacy
`_podcast` source files and every legacy/current record and transcript alias.
The importer excludes those source files, and validation rejects their return;
the current tree therefore contains 203 podcasts and 201 transcripts while the
immutable migration counts remain 205 and 203.

Source verification composes the overlays without weakening the migration
boundary. For a declared podcast, it validates the editorial manifest, removes
only the exact declared `description` from the candidate mapping, and then
compares every remaining field with the metadata deterministically reconstructed
from the immutable legacy checkout, including the seasonal sibling transcript
reference. The SHA-bound missing-media repair remains
unchanged and scoped to its own declared article and media outputs.

The accepted editorial and repair manifests use the seasonal episode paths.
Their target-file and provenance digests are recomputed from the moved files;
the public `legacy_path` values and canonical slugs are not changed.

`migration/editorial-overlays/2026-09-01-source-corrections.yaml` is the immutable
source-owned correction overlay for the five AI Shipping Blog link destinations
and the S24E06 artwork correction. It is pinned byte-for-byte by
`scripts/source_correction.py`. The article rows distinguish complete Markdown
destinations from complete HTML `href` values, including their exact line
contexts; a URL prefix, prose occurrence, or unbounded replacement is never
accepted. The podcast row allows only its `image` scalar, and the media row
requires a lossless rename of the exact 38,743-byte image. Every target path,
blob, and SHA-256 is pinned, and missing, extra, symlinked, or changed files
fail closed.
The manifest also pins the complete expected `git diff --name-status
--find-renames=100%` census for the source-side commit; the CI attestation
compares that census, the final commit, and its tree before publishing.

Run the source correction contract independently with:

```bash
make validate-source-correction
make attest-source-correction \
  COMMIT="$(git rev-parse HEAD)" \
  OUTPUT=.tmp/attestation/source-correction.json
```

The latter command is intended for a clean committed checkout; the emitted
attestation binds the exact replacement commit and Git tree to the pinned
correction manifest and target hashes.

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
`migration/migration.yaml`. Verification proves all 807 baseline media bytes, all
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
