#!/usr/bin/env python3
"""
Fuzzy search experiment v2 for ./database.db (tracks table).

Changes vs v1:
- Parse query into artist/title when possible (Artist - Title).
- Score artist and title separately, title-weighted combined score.
- Apply artist-mismatch penalty to reduce title-only false positives.
- Add edit/remix/VIP secondary check (edit_score) so base-track matches can be labeled BASE_ONLY.
- Classification: EXACT / BASE_ONLY / CANDIDATE / NO_MATCH.

Requires: pip install rapidfuzz
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz


# ---- Your queries (paste/edit as needed) ----
QUERIES = [
    "Sub Focus - Ecuador",
    "Marlon Hoffstadt - It's That Time (Dimension Remix)",
    "Fred again.., Skepta, PlaqueBoyMax - Victory Lap (Sudley Bootleg)",
    "Adapter & FRANCO BA - Malfunktion",
    "CamelPhat ft. Ali Love - Spektrum (Tharat Remix)",
    "Gold Panda - Untitled1000",
    "Babert - Time After Time (Extended Mix)",
    "Fourward - How (Instrumental)",
    "Wilkinson - Wash Away",
    "Wilkinson & Sub Focus - Take It Up",
    "Tony Romera - 2009",
    "Brandy & Monica - The Boy Is Mine + Fred Again - Hannah (the sun) (mixed)",
    "A Little Sound - Override [MINISTRY OF SOUND]",
    "Moko - Your Love (Culture Shock Remix) [MTA]",
    "Sub Focus & Metrik - Trip (VIP) [Intro Edit]",
    "John Summit & Sub Focus ft. Julia Church - Go Back (YDG Remix)",
    "Sub Focus ft. AR/CO - Vibration (One More Time) (VIP)",
    "Avicii - Levels (1991 Remix)",
    "Benny L - Memories",
    "Sub Focus & Dimension - Desire",
    "Subsonic - Ascend",
    "Sub Focus & Dimension ft. Jo Hill - Ready To Fly",
    "IRAH ft. Chase & Status - Gunfinger (Salute)",
    "Rova - Eyes On Me",
    "Kanine - Chemicals",
    "Sammy Virji - If U Need It (Camo & Krooked Remix)",
    "Sub Focus ft. Gene Farris - It's Time (VIP) (London Vocal Edit)",
    "Sub Focus - Wildfire (VIP)",
    "John Summit & Sub Focus ft. Julia Church - Go Back (D&B VIP)",
    "John Summit & Sub Focus ft. Julia Church - Go Back (YDG Remix)"
]


# ---------------- Normalization ----------------
_WS_RE = re.compile(r"\s+")
# Grab bracket contents for "edit tokens" extraction
_BRACKET_CONTENT_RE = re.compile(r"[\(\[\{]([^\)\]\}]*)[\)\]\}]")
# For "basic" normalization (remove brackets entirely)
_BRACKETED_RE = re.compile(r"[\(\[\{].*?[\)\]\}]")
_PUNCT_RE = re.compile(r"[^\w\s]")


def normalize_basic(s: str) -> str:
    """
    Aggressive normalizer:
    - lowercase
    - remove bracketed segments
    - remove punctuation
    - collapse whitespace
    """
    s = (s or "").strip().lower()
    if not s:
        return ""
    s = _BRACKETED_RE.sub(" ", s)
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def normalize_light(s: str) -> str:
    """
    Lighter normalizer:
    - lowercase
    - collapse whitespace
    - keep punctuation (helps some IDs / acronyms)
    """
    s = (s or "").strip().lower()
    s = _WS_RE.sub(" ", s).strip()
    return s


def tokenize_basic(s: str) -> List[str]:
    s = normalize_basic(s)
    return s.split() if s else []


# ---------------- Query parsing ----------------
def split_artist_title(query: str) -> Tuple[str, str]:
    """
    Best-effort parse:
    - If string contains " - " => left is artist, right is title.
    - Else if contains " – " (en dash) => same.
    - Else => artist="", title=query.
    """
    q = (query or "").strip()
    if not q:
        return "", ""
    for sep in (" - ", " – ", " — "):
        if sep in q:
            a, t = q.split(sep, 1)
            return a.strip(), t.strip()
    return "", q


# ---------------- Edit token extraction ----------------
EDIT_KEYWORDS = {
    # core
    "vip", "remix", "rmx", "edit", "intro", "instrumental", "bootleg", "flip", "rework",
    "version", "mix", "extended", "dub", "acapella", "acappella", "refix", "boot",
    # common variants
    "d&b", "dnb", "drum", "bass",
}

# Map variants -> canonical
EDIT_CANON = {
    "rmx": "remix",
    "d&b": "dnb",
    "drum": "dnb",
    "bass": "dnb",
    "acappella": "acapella",
    "boot": "bootleg",
}

def extract_edit_tokens(query: str) -> List[str]:
    """
    Pulls out edit/remix-related tokens from:
    - bracket contents: (VIP), (YDG Remix), [Intro Edit], etc.
    - plus standalone keywords anywhere in the string.
    Returns canonicalized, de-duped tokens in stable order.
    """
    q = (query or "").strip().lower()
    if not q:
        return []

    tokens: List[str] = []

    # 1) bracket content
    for m in _BRACKET_CONTENT_RE.finditer(q):
        inner = m.group(1) or ""
        for tok in tokenize_basic(inner):
            if tok in EDIT_KEYWORDS:
                tokens.append(EDIT_CANON.get(tok, tok))

    # 2) standalone keywords (outside brackets too)
    for tok in tokenize_basic(q):
        if tok in EDIT_KEYWORDS:
            tokens.append(EDIT_CANON.get(tok, tok))

    # de-dupe preserving order
    seen = set()
    out = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


# ---------------- Track model ----------------
@dataclass(frozen=True)
class TrackRow:
    id: int
    platform_id: str
    platform: str
    name: str
    artist: str

    # precomputed fields
    artist_norm: str
    title_norm: str
    name_light: str
    artist_light: str

    @property
    def display(self) -> str:
        bits = [self.artist, self.name]

        return " - ".join([b for b in bits if b])


def load_tracks(db_path: str) -> List[TrackRow]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            SELECT id, platform_id, platform, name, artist
            FROM tracks
            """
        )
        rows = cur.fetchall()
        out: List[TrackRow] = []
        for r in rows:
            name = str(r["name"] or "")
            artist = str(r["artist"] or "")
            out.append(
                TrackRow(
                    id=int(r["id"]),
                    platform_id=str(r["platform_id"]),
                    platform=str(r["platform"]),
                    name=name,
                    artist=artist,
                    artist_norm=normalize_basic(artist),
                    title_norm=normalize_basic(name),
                    name_light=normalize_light(name),
                    artist_light=normalize_light(artist),
                )
            )
        return out
    finally:
        conn.close()


# ---------------- Scoring ----------------
def score_artist_title(query_artist: str, query_title: str, track: TrackRow) -> Dict[str, float]:
    """
    Return component scores 0..100 for artist and title comparisons.
    Using token_set_ratio on basic-normalized strings is very robust for messy metadata.
    """
    qa = normalize_basic(query_artist)
    qt = normalize_basic(query_title)

    # If no artist provided in query, artist_score is None-ish (we’ll treat as 0 weight).
    artist_score = float(fuzz.token_set_ratio(qa, track.artist_norm)) if qa else 0.0
    title_score = float(fuzz.token_set_ratio(qt, track.title_norm)) if qt else 0.0

    # Also compute partial on title to help when titles include extra junk
    title_partial = float(fuzz.partial_ratio(qt, track.title_norm)) if qt else 0.0

    return {
        "artist": artist_score,
        "title": title_score,
        "title_partial": title_partial,
    }


def score_edit_tokens(edit_tokens: List[str], track: TrackRow) -> float:
    """
    Secondary check: if query mentions VIP/remix/edit/etc, see if track title contains similar markers.

    We compare the tokens string vs the *raw-ish* track name (light normalize).
    """
    if not edit_tokens:
        return 0.0

    needle = " ".join(edit_tokens).strip()
    hay = normalize_basic(track.name)  # keep bracket content in "name" because normalize_basic removes it;
                                       # but here track.name includes it; normalize_basic will remove bracket text.
                                       # Better: use light on name so bracket text remains visible.
    hay_light = track.name_light

    # Use token_set_ratio on light strings (preserves bracket tokens) but basic tokens for the needle
    # We'll normalize the hay lightly, and the needle basically.
    return float(fuzz.token_set_ratio(normalize_basic(needle), normalize_basic(hay_light)))


def combined_score(parts: Dict[str, float], has_artist: bool) -> float:
    """
    Title-weighted score with mild support from title_partial.
    Artist gets meaningful weight only when query supplies artist.
    """
    title = parts["title"]
    title_partial = parts["title_partial"]
    artist = parts["artist"]

    # Title dominates; partial gives slight boost when title match is a substring/variant.
    base_title = 0.80 * title + 0.20 * title_partial

    if not has_artist:
        return base_title

    # With artist present: 65% title, 35% artist
    return 0.65 * base_title + 0.35 * artist


def apply_artist_penalty(score: float, artist_score: float, has_artist: bool) -> float:
    """
    Reduce "title-only" false positives:
    - If query has artist but artist_score is weak, penalize.
    """
    if not has_artist:
        return score

    # Tuned to aggressively kill "Your Love" matching random artists, etc.
    if artist_score < 40:
        return score - 25
    if artist_score < 55:
        return score - 15
    if artist_score < 65:
        return score - 7
    return score


def classify(score: float, edit_tokens: List[str], edit_score: float) -> str:
    """
    Output labels:
    - EXACT: strong match and edit tokens (if any) are compatible
    - BASE_ONLY: strong core match but requested edit/remix/VIP doesn't appear
    - CANDIDATE: plausible but not confident
    - NO_MATCH: likely absent
    """
    strong = score >= 85
    mid = 75 <= score < 85

    if strong:
        if edit_tokens:
            return "EXACT" if edit_score >= 70 else "BASE_ONLY"
        return "EXACT"
    if mid:
        return "CANDIDATE"
    return "NO_MATCH"


def top_matches(
    query: str,
    tracks: List[TrackRow],
    top_n: int,
    min_score: float,
) -> List[Tuple[float, float, Dict[str, float], TrackRow, str]]:
    """
    Returns: (final_score, edit_score, parts_dict, track, label)
    """
    q = (query or "").strip()
    if not q:
        return []

    q_artist, q_title = split_artist_title(q)
    has_artist = bool(q_artist.strip())
    edit_tokens = extract_edit_tokens(q)

    scored: List[Tuple[float, float, Dict[str, float], TrackRow, str]] = []
    for t in tracks:
        parts = score_artist_title(q_artist, q_title, t)
        s = combined_score(parts, has_artist=has_artist)
        s = apply_artist_penalty(s, parts["artist"], has_artist=has_artist)

        e = score_edit_tokens(edit_tokens, t) if edit_tokens else 0.0
        label = classify(s, edit_tokens, e)

        if s >= min_score:
            scored.append((s, e, parts, t, label))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_n]


# ---------------- Printing ----------------
def print_results(query: str, results: List[Tuple[float, float, Dict[str, float], TrackRow, str]]) -> None:
    q_artist, q_title = split_artist_title(query)
    edit_tokens = extract_edit_tokens(query)

    print("=" * 120)
    print(f"QUERY: {query}")
    if q_artist:
        print(f"  parsed: artist='{q_artist}' | title='{q_title}'")
    else:
        print(f"  parsed: title='{q_title}' (no artist detected)")
    if edit_tokens:
        print(f"  edit tokens: {edit_tokens}")

    if not results:
        print("  (no matches above threshold)")
        return

    header = (
        f"{'rank':>4}  {'score':>7}  {'artist':>6}  {'title':>6}  {'t_part':>6}  "
        f"{'edit':>6}  {'label':>9}  {'id':>6}  {'platform':>10}  match"
    )
    print(header)
    print("-" * len(header))

    for i, (s, e, parts, t, label) in enumerate(results, start=1):
        print(
            f"{i:>4}  "
            f"{s:>7.2f}  "
            f"{parts['artist']:>6.1f}  "
            f"{parts['title']:>6.1f}  "
            f"{parts['title_partial']:>6.1f}  "
            f"{e:>6.1f}  "
            f"{label:>9}  "
            f"{t.id:>6}  "
            f"{t.platform[:10]:>10}  "
            f"{t.display}"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description="Fuzzy match test v2 against ./database.db tracks table")
    ap.add_argument("--db", default="./database.db", help="Path to sqlite db (default: ./database.db)")
    ap.add_argument("--top", type=int, default=5, help="Top N matches per query (default: 8)")
    ap.add_argument("--min", dest="min_score", type=float, default=25.0, help="Minimum score to print (default: 55)")
    ap.add_argument("--only", default=None, help="Only run queries containing this substring (case-insensitive)")
    args = ap.parse_args()

    tracks = load_tracks(args.db)
    print(f"Loaded {len(tracks)} tracks from {args.db}")

    only = (args.only or "").strip().lower() or None

    for q in QUERIES:
        if not q.strip():
            continue
        if only and only not in q.lower():
            continue
        res = top_matches(q, tracks, top_n=args.top, min_score=args.min_score)
        print_results(q, res)


if __name__ == "__main__":
    main()


