# RFC: Soulseek as a Download Source

## Context

PySync-Hub currently downloads audio exclusively through **yt-dlp**, hitting either
YouTube or SoundCloud directly (`youtube_download_service.py`,
`soundcloud_download_service.py`), or — for Spotify-sourced tracks with no direct
audio URL — falling back to a naive `ytsearch:` query that just takes the first
result (`spotify_download_service.py:63-72`). There is no scoring/ranking of search
candidates today, and no concept of a download *source* being independent from the
originating playlist *platform* (`Track.platform` drives `DownloadServiceFactory`
1:1).

The user wants Soulseek (P2P, generally much higher audio quality/bitrate and rarer
tracks) added as an additional, **toggleable** download source: when enabled, try
Soulseek first, and fall back to the existing YouTube/SoundCloud path if no good
match is found. This requires (a) research into how Soulseek can be driven
programmatically, (b) a design for where it plugs into the existing service/factory
architecture, and (c) a matching algorithm that also checks duration, since
Soulseek has no concept of "official audio" — many mislabeled/wrong-length files
circulate.

This plan is research + design only (RFC), not implementation, per the user's
request. It also proposes the settings/UI toggle and matching-algorithm design so
a future implementation pass has a clear spec.

---

## Part 1 — Research: how Soulseek integration actually works

**Soulseek has no official public API.** It's a proprietary P2P protocol
(documented by reverse-engineering, see Nicotine+'s
[SLSKPROTOCOL.html](https://nicotine-plus.org/doc/SLSKPROTOCOL.html)). Files are
transferred **directly peer-to-peer** — once you search and pick a result, your
client opens a direct connection (or an indirect one relayed via the central
server if the peer is behind NAT) to the peer who has the file and downloads it
straight from them. There is no central file host and no "download client" in the
sense of a separate app doing the transfer *for* you — but you do need a full
protocol-speaking client (handshake with the central server, peer messaging,
transfer state machine) because it's not a simple HTTP request.

**yt-dlp has no Soulseek extractor** — confirmed by dependency/code check; this
means the existing `_generate_yt_dlp_options` / `YoutubeDL(...).download()` pattern
that every other download service uses cannot be reused for Soulseek. A Soulseek
service needs its own client stack.

### Two integration options

1. **`slskd`** (recommended) — a self-hosted, actively maintained daemon
   ([github.com/slskd/slskd](https://github.com/slskd/slskd)) that speaks the full
   Soulseek protocol and exposes it as a **REST + WebSocket API** over HTTP, plus a
   web UI. You run it once (Docker container, or a bundled/launched local process
   on Windows/Linux) with a Soulseek account's credentials, and PySync-Hub's
   backend talks to it over `localhost` HTTP instead of implementing the raw binary
   protocol itself. A maintained Python wrapper already exists,
   **`slskd-api`** ([PyPI](https://pypi.org/project/slskd-api/)), covering search,
   transfers/downloads, and status polling.
   - Search: `slskd.searches.search_text(...)` → poll until complete → 
     `slskd.searches.search_responses(search_id)`.
   - Download: `slskd.transfers.enqueue(username, files=[{filename, size}])`, then
     poll `slskd.transfers.get_downloads()` until `state == "Completed, Succeeded"`,
     then the file is on disk in slskd's own download directory (need to move/copy
     it into `Config.DOWNLOAD_FOLDER`).
   - This mirrors exactly how the well-known **Soularr** project (Lidarr +
     slskd-api) works, so it's a proven pattern.
2. **Raw protocol library** (e.g. `aioslsk`, `Soulseek.NET`-equivalents in Python)
   — talk to the Soulseek network directly with no separate daemon/process. Fewer
   moving parts for the end user (no Docker/daemon to run), but far less mature
   tooling in Python, and PySync-Hub would own the full protocol implementation
   (peer connection handling, NAT traversal via indirect `ConnectToPeer`, etc.) —
   high risk/effort, not justified for this feature.

**Recommendation: use `slskd`.** It's the de facto standard way third-party tools
integrate with Soulseek today (Soularr, various *arr-stack tools), has a
maintained REST API and Python client, and isolates all the P2P protocol
complexity outside of PySync-Hub's own process. The tradeoff is that the user must
run an `slskd` instance (Docker container or local binary) with their own Soulseek
account credentials, and configure PySync-Hub to point at its URL + API key —
this is comparable to how the app already asks for Spotify/SoundCloud API
credentials in Settings, just one more external dependency to stand up.

### What Soulseek/slskd search results expose

Each search response is a batch of one-uploader results
(`slskd_api` `SearchResponseItem`), containing per-uploader stats and a list of
files:

- **Per uploader (peer):** `username`, `hasFreeUploadSlot` (bool — false often
  means you'll be **queued** behind other downloaders), `queueLength` (position/
  size of that user's upload queue — a proxy for expected wait time),
  `uploadSpeed` (bytes/sec, their measured upload bandwidth), `fileCount`,
  `lockedFileCount`/`lockedFiles` (**this is the "private/locked" signal** — some
  users share files but mark them "locked" so they aren't downloadable until you
  are, e.g., a mutual friend/some clients gate this; locked files show up
  separately and should be treated as unusable and filtered out).
- **Per file:** `filename`, `size` (bytes), `bitRate`, `bitDepth`, `sampleRate`,
  and `length` (duration in seconds) — this is exactly the field needed for
  duration-based matching.

So yes: quality (bitrate/format/sample rate), speed/"seeder"-equivalent
(uploadSpeed + queueLength + hasFreeUploadSlot as the closest Soulseek analogue
to torrent seeder count — Soulseek has no seeder concept, just single-source P2P
per file), and lock/private status are all directly available in the search
response with no extra calls needed.

---

## Part 2 — Architecture: where this plugs in

Reuse the existing `BaseDownloadService` abstract-class + `DownloadServiceFactory`
pattern (`app/services/download_services/`), matching how `spotify_download_service.py`
already does "search then download" (vs. Youtube/SoundCloud's "direct URL"
pattern):

- **New `SoulseekDownloadService(BaseDownloadService)`**
  (`app/services/download_services/soulseek_download_service.py`) implementing
  `download_track_with_ytdlp(cls, track)` (same abstract method name/contract as
  other services, despite not using yt-dlp — keeps `BaseDownloadService.download_track`
  and `download_playlist` reusable unchanged). Internally:
  1. Build query `f"{track.artist} {track.name}"`.
  2. Call a new `SoulseekService` (see below) to search + pick best match.
  3. If no acceptable match (score below threshold, or no results) → raise a
     specific `SoulseekNoMatchError` so the caller can fall back.
  4. Enqueue the chosen file for download via slskd, poll to completion.
  5. Move/rename the completed file into `Config.DOWNLOAD_FOLDER`, run it through
     the **existing** `FileDownloadUtils.embed_track_metadata()` (already handles
     ID3 tags + cover art, format-agnostic) and `track.set_download_location()`.
- **New `SoulseekService`** (`app/services/platform_services/soulseek_service.py`,
  or a slimmer non-`BasePlatformService` client since Soulseek has no "playlists")
  wrapping `slskd_api.SlskdClient`: `search(query, timeout)`, and the scoring/
  selection logic described in Part 3.
- **New dependency**: add `slskd-api` to `requirements.txt`.

### The "toggle + fallback" behavior (new concept — doesn't exist today)

Today, download source == `track.platform`, decided once at import time, with no
per-download-attempt choice. This feature needs a **fallback chain**, which is new:

- Add a global setting `PREFER_SOULSEEK` (bool, default `false`) — a straightforward
  checkbox toggle, not per-playlist (per user's ask: "a toggle for whether to use
  soulseek or fallback to youtube/soundcloud").
- In `download_worker.py`'s `_download_worker` (and/or by updating it to finally use
  `DownloadServiceFactory` instead of its current duplicated if/elif — worth
  cleaning up as part of this change), before dispatching to the
  platform-specific service: if `Config.PREFER_SOULSEEK` is true, first attempt
  `SoulseekDownloadService.download_track(track)`; on `SoulseekNoMatchError` (or any
  download failure), fall through to the existing platform-specific service
  unchanged. This keeps Soulseek as a pure best-effort first attempt layered in
  front of the current, proven logic — no change to existing YouTube/SoundCloud/
  Spotify code paths themselves.
- This fallback wrapping is best implemented once, in `BaseDownloadService.download_track`
  or in the worker, rather than duplicated per platform.

### Settings additions

- `config.py` `DEFAULT_SETTINGS`/`Config` and `routes/settings.py`
  `DEFAULT_SETTINGS`: add `SOULSEEK_ENABLED` (bool), `SLSKD_URL` (e.g.
  `http://localhost:5030`), `SLSKD_API_KEY`.
- `SettingsPage.js`: new "Soulseek" section — a toggle switch (first UI toggle in
  the app; existing settings are all plain text fields) plus text inputs for slskd
  URL/API key, and a "Test Connection" button (calls a new lightweight
  `GET /api/soulseek/status` route that pings `slskd_api.SlskdClient(...).application.state()`).

---

## Part 3 — Matching algorithm (search + duration check)

Mirror the existing YouTube-search pattern (`ytsearch{limit}:` → take first result,
`spotify_download_service.py:63-72` / `youtube_service.py:195-229`) but layer in
real scoring, reusing the **existing rapidfuzz-based scoring utilities and trained
logistic-regression model** already built for tracklist matching
(`app/utils/feature_scoring_utils.py`, `tracklist_prediction_service.py`) instead
of inventing new scoring from scratch.

### Reusing the existing LR model (`TracklistPredictionService.predict`)

`tracklist_prediction_service.py:86-103` already implements a small, fixed
logistic-regression classifier: 7 hand-built features
(`FeatureScores` — `global_token_set`, `artist_set`, `title_sort`,
`remix_crosscheck`, `vip_conflict`, `structural_conf`, `length_similarity`) go
through `sigmoid(w·x + b)` with hardcoded, presumably offline-trained weights, to
produce a 0.0–1.0 confidence score (≥0.5 = confident match, the app already treats
<0.1 as "no match" in `predict_tracklist_entry_match`). It was trained for
matching a free-text DJ-tracklist line against a DB track's `"{artist} - {name}"`,
which is structurally very close to matching a Soulseek filename against the same
DB track — both are "messy real-world string vs. clean DB string" problems. This
makes it a strong candidate to reuse rather than re-deriving fuzzy-match logic:

- Parse each Soulseek result's filename/folder path into an `artist`/`title`
  guess (strip extension, split on the same `" - "` separator convention the
  tracklist cleaner already assumes — reuse
  `app/utils/tracklist_cleaning_utils.py`'s helpers, e.g.
  `extract_version_from_title`, where applicable) so it can be fed through the
  **same** `calculate_feature_scores_tracks`-style feature computation.
- Compute `global_token_set`, `artist_set`, `title_sort`, `remix_crosscheck`
  exactly as `feature_scoring_utils.py` does today, comparing the parsed
  Soulseek filename against `f"{track.artist} - {track.name}"`.
- `vip_conflict` and `structural_conf` are tracklist-specific concepts (VIP edits
  called out in DJ sets; "is this raw tracklist line structured like `Artist -
  Title`") that only loosely apply to Soulseek filenames — as a pragmatic v1,
  compute `structural_conf` the same way (Soulseek filenames are almost always
  `Artist - Title` structured, so this stays meaningful) and fix `vip_conflict`
  to its neutral value (0) rather than force a new heuristic, since Soulseek
  gives no separate "is this a VIP" signal to cross-check against.
- Feed the resulting `FeatureScores` through the **existing, unmodified**
  `TracklistPredictionService.predict()` to get a `text_confidence` score in the
  same 0–1 space the rest of the app already uses and tunes thresholds against —
  this avoids inventing a second, incompatible scoring scale.

### Signals the LR model was never trained on: duration + Soulseek-specific quality

The LR model's weights are fixed (fit offline on tracklist data) and have no
input for audio duration, bitrate, or peer/queue stats — appending new features
to the vector would silently invalidate the trained weights. So these are kept as
a **separate gating/adjustment layer on top of** the reused LR text-confidence,
not merged into the model:

1. Query slskd: `search_text(f"{track.artist} {track.name}")`, wait for the search
   to complete (poll `searches.state(search_id)`), collect all `SearchResponseItem`s.
2. Flatten to candidate files, **filtering out**:
   - Locked/private files (`lockedFiles`, `lockedFileCount` > 0 entries) —
     unusable without becoming a "friend" of that user first.
   - Non-audio extensions (filter by `.mp3`/`.flac`/`.wav`/`.m4a`/etc.).
   - Zero free slot **and** excessively long `queueLength` (configurable
     threshold) — avoids picking a file that will queue for hours.
3. For each remaining candidate, compute `text_confidence` via the reused LR
   model above, then:
   - **Duration gate** (the safeguard against wrongly-labelled files the user
     asked for): if `abs(file.length - track.duration_ms/1000)` exceeds a
     tolerance (e.g. 5–10s), reject the candidate outright regardless of
     `text_confidence` — mislabeled Soulseek files are common enough that this
     should be a hard filter, not just a score penalty. Tracks with unknown
     duration skip this gate.
   - **Quality/speed tiebreaker**: among candidates that pass the duration gate
     and have `text_confidence` within a small margin of each other, prefer
     higher `bitRate`/`bitDepth` (FLAC/320kbps over 128kbps) and better peer
     stats (`hasFreeUploadSlot`, lower `queueLength`, higher `uploadSpeed`) —
     applied as a secondary sort key, not blended into the LR score.
4. Pick the highest `text_confidence` candidate that passed the duration gate,
   using quality/speed as the tiebreaker; require `text_confidence >= 0.5`
   (matching the existing "confident match" threshold used elsewhere) to accept
   it at all. No acceptable candidate → raise `SoulseekNoMatchError` → triggers
   the YouTube/SoundCloud fallback described in Part 2.

**Future work, not v1**: the LR model's weights only reflect tracklist-matching
behavior; if false-positive/negative rates on real Soulseek matches turn out
poor, a proper fix would be collecting labeled Soulseek match/non-match data and
retraining a model that includes duration/quality as first-class features rather
than bolting them on as a gate — flagged here rather than attempted now since no
training data exists yet.

---

## Verification plan (for the future implementation phase)

- Unit-test the scoring function with synthetic Soulseek search-result fixtures
  (correct match, wrong-duration match, locked file, low-quality vs high-quality
  duplicate) to confirm it picks the expected candidate and rejects bad ones.
- Manual/integration test: run a local `slskd` Docker instance, enable the
  Soulseek toggle in Settings, download a playlist known to have Soulseek
  coverage, confirm the file lands in `music_downloads/` with correct ID3 tags,
  and confirm a track *not* found on Soulseek correctly falls back to
  YouTube/SoundCloud without user-visible failure.
- Verify the "Test Connection" settings button correctly reports slskd
  reachability/auth failures distinctly (bad URL vs bad API key vs slskd not
  running).

---

## Confirmed decisions

- **slskd setup**: v1 requires the user to run their own `slskd` instance
  (Docker/binary) and paste its URL + API key into Settings — no bundling/
  auto-launch, consistent with how Spotify/SoundCloud credentials work today.
- **Toggle scope**: global only (`SOULSEEK_ENABLED` / `PREFER_SOULSEEK`), no
  per-playlist override — matches the request as stated and needs no schema
  change.

## Open question for the user (not yet resolved)

- Preferred audio quality ceiling — do we want a max-bitrate/format preference
  (e.g. prefer FLAC) exposed as a setting, or keep quality scoring purely internal
  to the matching algorithm?
