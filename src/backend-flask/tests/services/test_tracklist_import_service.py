#!/usr/bin/env python3
"""
Quick fuzzy-search test harness for ./database.db (tracks table).

- Loads all tracks.
- For each query string, computes fuzzy scores against candidate strings.
- Prints top matches (with algorithm scores) so you can evaluate robustness.

Requires: pip install rapidfuzz
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from dataclasses import dataclass
from typing import Iterable, List, Tuple, Dict, Any

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


# ---- Normalization helpers ----
_WS_RE = re.compile(r"\s+")
_BRACKETED_RE = re.compile(r"[\(\[\{].*?[\)\]\}]")  # remove bracketed annotations (remix, labels, etc.)
_PUNCT_RE = re.compile(r"[^\w\s]")  # keep letters/numbers/underscore and whitespace


def normalize_basic(s: str) -> str:
    """
    A fairly aggressive normalizer for fuzzy matching:
    - lowercase
    - remove bracketed text ( (...) / [...] / {...} )
    - remove punctuation
    - collapse whitespace
    """
    s = (s or "").strip().lower()
    if not s:
        return ""
    # s = _BRACKETED_RE.sub(" ", s)
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def normalize_light(s: str) -> str:
    """
    Lighter normalizer:
    - lowercase
    - collapse whitespace
    - keep punctuation (sometimes helps with IDs)
    """
    s = (s or "").strip().lower()
    s = _WS_RE.sub(" ", s).strip()
    return s


# ---- Data model for loaded rows ----
@dataclass(frozen=True)
class TrackRow:
    id: int
    platform_id: str
    platform: str
    name: str
    artist: str

    @property
    def display(self) -> str:
        # what you'll see in output
        bits = [self.artist, self.name]
        return " - ".join([b for b in bits if b])

    @property
    def candidate_full(self) -> str:
        # what we match against
        # include both common "artist - title" and "title - artist" style signals
        a = self.artist or ""
        n = self.name or ""
        return f"{a} - {n} | {n} - {a} | {a} {n}".strip()


# ---- DB loading ----
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
            out.append(
                TrackRow(
                    id=int(r["id"]),
                    platform_id=str(r["platform_id"]),
                    platform=str(r["platform"]),
                    name=str(r["name"] or ""),
                    artist=str(r["artist"] or ""),
                )
            )
        return out
    finally:
        conn.close()


# ---- Scoring ----
def score_pair(query: str, candidate: str) -> Dict[str, float]:
    """
    Compute a few useful fuzzy scores.

    RapidFuzz scores are 0..100.
    """
    # two different normalizations so you can see what helps/hurts
    q_basic = normalize_basic(query)
    c_basic = normalize_basic(candidate)

    q_light = normalize_light(query)
    c_light = normalize_light(candidate)

    # token-based is often best for "Artist - Title (Remix)" types of strings
    return {
        "token_set": float(fuzz.token_set_ratio(q_basic, c_basic)),
        "token_sort": float(fuzz.token_sort_ratio(q_basic, c_basic)),
        "partial": float(fuzz.partial_ratio(q_basic, c_basic)),
        "wratio": float(fuzz.WRatio(q_light, c_light)),
    }


def combined_score(scores: Dict[str, float]) -> float:
    """
    Single number for ranking.

    You can tweak weights after you eyeball results.
    """
    return (
        0.45 * scores["token_set"]
        + 0.20 * scores["wratio"]
        + 0.20 * scores["partial"]
        + 0.15 * scores["token_sort"]
    )


def top_matches(
    query: str,
    tracks: List[TrackRow],
    limit: int,
    min_score: float,
) -> List[Tuple[float, TrackRow, Dict[str, float]]]:
    q = (query or "").strip()
    if not q:
        return []

    scored: List[Tuple[float, TrackRow, Dict[str, float]]] = []
    for t in tracks:
        s = score_pair(q, t.candidate_full)
        cs = combined_score(s)
        if cs >= min_score:
            scored.append((cs, t, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]


def print_results(query: str, results: List[Tuple[float, TrackRow, Dict[str, float]]]) -> None:
    print("=" * 110)
    print(f"QUERY: {query}")
    if not results:
        print("  (no matches above threshold)")
        return

    header = f"{'rank':>4}  {'combined':>8}  {'token_set':>9}  {'wratio':>7}  {'partial':>7}  {'token_sort':>9}  {'id':>6}  {'platform':>10}  match"
    print(header)
    print("-" * len(header))

    for i, (cs, t, s) in enumerate(results, start=1):
        print(
            f"{i:>4}  "
            f"{cs:>8.2f}  "
            f"{s['token_set']:>9.2f}  "
            f"{s['wratio']:>7.2f}  "
            f"{s['partial']:>7.2f}  "
            f"{s['token_sort']:>9.2f}  "
            f"{t.id:>6}  "
            f"{t.platform[:10]:>10}  "
            f"{t.display}"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description="Fuzzy match test against ./database.db tracks table")
    ap.add_argument("--db", default="./database.db", help="Path to sqlite db (default: ./database.db)")
    ap.add_argument("--top", type=int, default=5, help="Top N matches per query (default: 8)")
    ap.add_argument("--min", dest="min_score", type=float, default=5.0, help="Minimum combined score to print (default: 55)")
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
        res = top_matches(q, tracks, limit=args.top, min_score=args.min_score)
        print_results(q, res)


if __name__ == "__main__":
    main()
