# Podcast identity and missing episode restoration (2026-11-15)

This source correction completes website issue #162 and Hub intake 9a6ec0b2.
No runtime exceptions or hardcoded alias maps are needed: production reads synced
source rows. Reverting this content commit reverses the mappings.

## Season 3

Publisher feed: https://anchor.fm/s/41286f68/podcast/rss (discovered through Apple's
lookup API for show 1541710331; inspected 2026-11-15).

| Source identity | RSS publication (UTC) | RSS season / episode | Canonical decision |
| --- | --- | --- | --- |
| Data Observability — Barr Moses | 2021-04-23 17:00 | 3 / 3 | unchanged |
| Effective Communication with Business for Data Professionals — Lior Barak | 2021-04-30 17:00 | 3 / episode omitted | S03E04 |
| What I Learned After Interviewing 300 Data Scientists — Oleg Novikov | 2021-05-07 17:00 | 3 / **5** | **S03E05** |
| From Physics to Machine Learning — Tatiana Gabruseva | 2021-05-14 17:00 | 3 / 6 | unchanged |

Oleg's publisher GUID is `05b6b633-aae8-4bec-872b-beef313a9922`; Lior's is
`f3b3e084-7cba-4132-90c3-9c4ef73ec2c7`. The legacy/current records share an
incorrect E04 value but are distinct recordings, confirmed by guest and platform:

- Oleg: YouTube `AYi7b-8GPm4`, Spotify `406wN6xDkYPyLS8i9fUJL5`,
  Apple episode `1000520681105`, legacy slug `data-science-interview-and-cv-guide`.
- Lior: YouTube `gqroEsTyLD0`, Spotify `4RF592cRWxHgcXbx6pV0Ja`,
  Apple episode `1000519463715`, legacy slug `data-translator-role-and-data-strategy`.

The explicit RSS E05 and consecutive weekly release order support correcting Oleg
to E05 and retaining Lior at E04. Lior's number is inferred from the existing E04
and neighboring feed entries; no conflicting platform identity was found. Move
both metadata and transcripts to ordinary E04/E05 siblings. Preserve slugs,
legacy URLs, platform IDs, transcript segments, and unrelated dates.

## Season 25

Copied metadata, resources and transcript segments from the legacy repository
at `6265f8fe8d9e68575281c7dcb8b8f1f01a6a7697`:

| Episode | Guest | YouTube | Spotify | RSS publication (UTC) |
| --- | --- | --- | --- | --- |
| S25E07 | Dewang Sultania | T1R-IfYrRFY | 6KBRD5TGLggGuPFvvXGPyR | 2026-10-16 17:00 |
| S25E08 | Miguel Otero Pedrido | xC5lqvfSfLU | 5J8royMpnXL43xtJ9y87qA | 2026-11-13 18:00 |
| S25E09 | Tejas Kumar | oWVmQDqZ7tw | 7kBm1cbAlWxKeclurWgz7b | 2026-10-23 17:00 |

RSS explicitly confirms all three season/episode numbers, even though E08 was
published after E09. Keep the publisher numbering. E07 artwork is copied byte
for byte from legacy. E08/E09 have no legacy `image`; use the actual corresponding
YouTube `https://i.ytimg.com/vi/<video-id>/maxresdefault.jpg` thumbnail, inspected
for the matching title and guest. No generated artwork or invented transcript.

## CI scope

The existing workflow was red on main because a frozen migration attestation
was run against later editorial additions (212 podcasts versus 203). CI now
runs `make check` on the exact PR head, including the restored 215-episode
catalogue. It separately verifies and attests the immutable migration at its
last green release `9ad8f5001426734a4e3854c1e1936009fa774868` against its original
legacy source `ee43d3fa0929faf691178d79f19528e6f15a83e5`.
The historical artifact identifies its own commit/tree; it does not purport to
attest current content. Current schema, references, media and source-correction
validation and the complete test suite still run at HEAD.
