import ftfy
from anyascii import anyascii
import unicodedata
import re

""" Utils for cleaning and processing tracklists. """

def split_tracks(tracklist: str) -> list:
    """ Split a tracklist string into individual tracks. """       
    if not tracklist:
        return []
    normalized = tracklist.replace("w/", "\n")
    return [track.strip() for track in normalized.splitlines() if track.strip()]


def clean_track_unicode(track:str) -> str:
    """ Clean up unicode and mojibake. Replace unicode with ascii equivalents or removes all together """
    # 1) Fix mojibake like "MarlÃ¸n" → "Marløn"
    track = ftfy.fix_text(track)
    # 2) Normalize unicode (separates accents from letters)
    track = unicodedata.normalize("NFKD", track)
    # 3) Strip accents (ü → u, ø → o, etc.)
    track = "".join(c for c in track if not unicodedata.combining(c))
    # 4) Normalize dash variants to ASCII "-"
    # Covers –, —, ‐, −, etc.
    track = re.sub(r"[‐-‒–—−]", "-", track)
    # 5) Normalize weird spaces
    track = re.sub(r"[\u00A0\u2000-\u200B\u202F\u205F\u3000]", " ", track)
    # 6) Collapse repeated spaces
    track = re.sub(r"\s+", " ", track)
    # 7) Last catch, convert to pure ASCII
    return track.encode('ascii', 'ignore').decode().strip()


def clean_track_prefix(track:str) -> str:
    """ Remove common prefixes, usually timestamps, bluepoints, or numbering. """
    s = track.strip()

    # --- Remove leading bullets (•, -, etc.) ---
    s = re.sub(r"^[\u2022•\-\*]+\s*", "", s)

    # --- Remove bracketed timestamps like [01:45] ---
    s = re.sub(r"^\[\s*\d{1,2}:\d{2}(?::\d{2})?\s*\]\s*", "", s)

    # --- Remove numbered list prefixes like "3. " or "4. " ---
    s = re.sub(r"^\d+\.\s*", "", s)

    # --- Remove time ranges like "15:00 to 18:00 :" ---
    s = re.sub(r"^\d{1,2}:\d{2}\s+to\s+\d{1,2}:\d{2}\s*:\s*", "", s, flags=re.I)

    # --- Remove leading timestamps like 0:12, 45:57, 1:01:20 ---
    s = re.sub(r"^\d{1,2}:\d{2}(?::\d{2})?\s*", "", s)

    # --- Remove separators that often follow timestamps ---
    s = re.sub(r"^[-–—:]+\s*", "", s)

    return s.strip()


def is_unidentified_track(track:str) -> bool:
    """ Checks if a track is unidentified. E.g "artist - ID" """
    track = track.strip()

    # Exact "ID"
    if re.fullmatch(r"ID", track, flags=re.IGNORECASE):
        return True
    
    # Split into artist / title if possible
    if " - " in track:
        _, title = track.split(" - ", 1)
    else:
        title = track
    title = title.strip()

    # Title must START with "ID" as a whole word
    # and not be something like "ID remix" or "ID edit"
    if re.match(r"^ID(\b|$)", title, flags=re.IGNORECASE):
        # Disallow musical descriptors after ID
        if not re.search(r"\b(remix|edit|vip|mix|bootleg|version)\b", title, re.I):
            return True

    return False

def extract_artist_and_title(track:str, assume_artist_first:bool = True) -> tuple[str, str]:
    """ Extract artist and title from a track string using common matching patterns. 
    
    :param assume_artist_first: If True, assumes the format "Artist - Title". If False, assumes "Title - Artist". todo: implement
    """
    if ' - ' in track:
        artist, title = track.split(' - ', 1)
        return artist.strip(), title.strip()
    return '', track.strip()


