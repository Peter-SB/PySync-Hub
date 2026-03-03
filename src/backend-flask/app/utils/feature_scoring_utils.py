from __future__ import annotations

import re
from rapidfuzz import fuzz

from app.utils.tracklist_cleaning_utils import extract_version_from_title

LOW_VALUE_VERSION_PATTERN = re.compile(
    r"\b(extended|original|origional)\s+mix\b",
    re.IGNORECASE,
)

def _normalize_whitespace(text: str) -> str:
    text = text or ""
    return re.sub(r"\s+", " ", text).strip()


def _normalize_forfuzz(text: str) -> str:
    text = _normalize_whitespace(text).lower()
    return text


def calculate_global_token_set_score(str_a: str, str_b: str) -> float:
    """Feature 1: Global Token Set (fuzz.token_set_ratio)."""
    return fuzz.token_set_ratio(_normalize_forfuzz(str_a), _normalize_forfuzz(str_b))


def calculate_artist_set_score(artist_a: str, artist_b: str) -> float:
    """Feature 2: Artist Set Score (fuzz.token_set_ratio)."""
    return fuzz.token_set_ratio(_normalize_forfuzz(artist_a), _normalize_forfuzz(artist_b))


def calculate_title_sort_score(title_a: str, title_b: str) -> float:
    """Feature 3: Title Sort Score (fuzz.token_sort_ratio)."""
    return fuzz.token_sort_ratio(_normalize_forfuzz(title_a), _normalize_forfuzz(title_b))


def calculate_remix_artist_crosscheck(remixer: str, other_full: str) -> float:
    """Feature 4: Remix Artist Cross-Check (fuzz.partial_ratio). If not remix then assume a match"""
    if not remixer or not other_full:
        return 100
    return fuzz.partial_ratio(_normalize_forfuzz(remixer), _normalize_forfuzz(other_full))

# def calculate_version_similarity(version_a: str, version_b: str) -> int:
#     """Feature 5: Version Similarity (fuzz.ratio)."""

#     def _strip_low_value_version_tokens(version: str) -> str:
#         version = _normalize_forfuzz(version)
#         version = LOW_VALUE_VERSION_PATTERN.sub("", version)
#         return _normalize_whitespace(version)

#     cleaned_a = _strip_low_value_version_tokens(version_a)
#     cleaned_b = _strip_low_value_version_tokens(version_b)
#     if not cleaned_a and not cleaned_b:
#         return 100
#     return fuzz.ratio(cleaned_a, cleaned_b)
#   
#     ^^^ NO NEED ALREADY HANDLED IN tracklist_cleaning_utils.py ^^^
#     for match in BRACKET_PATTERN.finditer(full_title):
#         content = match.group(0)[1:-1]  # remove () or []
#         if VERSION_KEYWORDS.search(content):
#             version = content
#             title = title.replace(match.group(0), "").strip()
#             break


def calculate_vip_conflict(is_vip_a: bool, is_vip_b: bool) -> int:
    """Feature 6: VIP Conflict (binary)."""
    return 1 if bool(is_vip_a) != bool(is_vip_b) else 0


def calculate_structural_confidence(raw_track: str, separator_token: str = " - ") -> float:
    """Feature 7: Structural Confidence (0.2 to 1.0)."""
    if not raw_track:
        return 0.2
    if separator_token and separator_token in raw_track:
        return 1.0
    if re.search(r"\s-\s|\s-|-\s", raw_track):
        return 0.6
    return 0.2


def calculate_length_penalty(str_a: str, str_b: str) -> float:
    """Feature 8: Length Penalty (normalized length similarity)."""
    a = _normalize_whitespace(str_a)
    b = _normalize_whitespace(str_b)
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 1.0
    diff = abs(len(a) - len(b))
    return max(0.0, 1.0 - (diff / max_len))


def calculate_feature_scores_tracks(tracklist_entry: "TracklistEntry",
                                    database_track: "DatabaseTrack" 
                                    ) -> dict[str, float | int]:
    """Calculate all feature scores for a given TracklistEntry and DatabaseTrack."""
    db_name = f"{database_track.artist} - {database_track.name}"

    global_token_set = calculate_global_token_set_score(tracklist_entry.prefix_cleaned_entry, db_name)
    artist_set = calculate_artist_set_score(tracklist_entry.artist, database_track.artist)
    title_sort = calculate_title_sort_score(tracklist_entry.full_title, database_track.name)
    
    db_remix_artist = extract_version_from_title(database_track.name)
    remix_crosscheck = calculate_remix_artist_crosscheck(tracklist_entry.version_artist, db_name)
    remix_crosscheck_reverse = calculate_remix_artist_crosscheck(db_remix_artist, f"{tracklist_entry.artist} - {tracklist_entry.full_title}")
    remix_crosscheck = min(remix_crosscheck, remix_crosscheck_reverse)


    vip_conflict = calculate_vip_conflict(tracklist_entry.is_vip, database_track.name.lower().find("vip") != -1)
    structural_conf = calculate_structural_confidence(tracklist_entry.full_tracklist_entry)
    length_similarity = calculate_length_penalty(tracklist_entry.prefix_cleaned_entry, db_name)
    return{
        "global_token_set": global_token_set,
        "artist_set": artist_set,
        "title_sort": title_sort,
        "remix_crosscheck": remix_crosscheck,
        "vip_conflict": vip_conflict,
        "structural_conf": structural_conf,
        "length_similarity": length_similarity
    }
