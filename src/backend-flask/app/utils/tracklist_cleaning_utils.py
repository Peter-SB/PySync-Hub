import ftfy
import unicodedata
import re

""" Utils for cleaning and processing tracklists. """


JUNK_PATTERNS = [
        r'\s*-\s*Free Download\s*',
        r'\s*\[Free Download\]\s*',
        r'\s*\(Free Download\)\s*',
        r'\s*FREE DOWNLOAD\s*',
        r'\s*-\s*FREE DOWNLOAD\s*',
        r'\s*\[FREE DL\]\s*',
        r'\s*\(FREE DL\)\s*',
        r'\s*FREE DL\s*',
        r'\s*-\s*FREE DL\s*',
        r'\s*\[Out Now\]\s*',
        r'\s*\(Out Now\)\s*',
        r"\bUNRELEASED\b",
        r"\bCOMING SOON\b",
        r"\bEXCLUSIVE\b",
    ]

VERSION_KEYWORDS = re.compile(r"remix|rmx|bootleg|edit|vip|dub|dubplate|mix|cut|version|rework", re.IGNORECASE)
BRACKET_PATTERN = re.compile(r"(\([^)]+\)|\[[^\]]+\])")
DASH_VERSION_PATTERN = re.compile(r"\s*-\s*(.+)$")

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


def remove_label_info(track: str) -> str:
    """ Remove label/catalog info from the end of a track string. Usually in square brackets. E.g " XYZ [LABEL]" 
    Will never have a version keyword though, this indicates its a version/remix not a label."""
    s = track
    s = re.sub(r"\s*\[([^\]]*?(?!" + VERSION_KEYWORDS.pattern + r")[^\]]*?)\]\s*$", "", s, flags=re.IGNORECASE)
    return s.strip()


def remove_junk_tags(track: str) -> str:
    """ Remove common junk tags such as: "FREE DOWNLOAD", "UNRELEASED", "FREE DL", "OUT NOW", etc. """
    s = track
    for pattern in JUNK_PATTERNS:
        s = re.sub(pattern, "", s, flags=re.IGNORECASE)

    # Collapse multiple spaces
    s = re.sub(r"\s{2,}", " ", s)

    return s.strip()


def is_unidentified_track(track: str) -> bool:
    """ Checks if a track is unidentified. E.g "artist - ID" """
    track = track.strip()

    if not track:
        return True

    if track.lower() == "id":
        return True
    
    return False

    # Exact "ID"
    # if re.fullmatch(r"ID", track, flags=re.IGNORECASE):
    #     return True

    # # Track starts with ID (e.g. "ID - ID", "ID (unreleased)")
    # if re.match(r"^ID(\b|$)", track, flags=re.IGNORECASE):
    #     if not re.search(r"\b(remix|edit|vip|mix|bootleg|version)\b", track, re.I):
    #         return True
    
    # # Split into artist / title if possible
    # if " - " in track:
    #     _, title = track.split(" - ", 1)
    # else:
    #     title = track
    # title = title.strip()

    # # Title must START with "ID" as a whole word
    # # and not be something like "ID remix" or "ID edit"
    # if re.match(r"^ID(\b|$)", title, flags=re.IGNORECASE):
    #     # Disallow musical descriptors after ID
    #     if not re.search(r"\b(remix|edit|vip|mix|bootleg|version)\b", title, re.I):
    #         return True

    # return False

def extract_artist_and_title(
        track:str, 
        assume_artist_first:bool = True,
        separator_token: str = " - ") -> tuple[str, str]:
    """ Extract artist and title from a track string using common matching patterns. 
    
    :param assume_artist_first: If True, assumes the format "Artist - Title". If False, assumes "Title - Artist".
    :param separator_token: The token used to separate artist and title. Default is " - ".

    todo: support edge case " artist- title" no space around dash. Note: dont include hyphenated words/titles
    """
    artist = ''
    title = track
    if separator_token in track:
        artist, title = track.split(separator_token, 1)
        
    if not assume_artist_first:
        title, artist = artist, title
        
    return artist.strip(), title.strip()
    

def extract_version_from_title(title: str) -> str:
    """ Extract version/remix info from a track title. E.g "Song Name (Artist Remix)" → "Artist Remix" """
    match = re.search(r"\(([^)]+)\)$", title)
    if match:
        return match.group(1).strip()
    return ""


def extract_title_and_version(full_title: str):
    title = full_title
    version = ""

    # --- Step 1: check bracketed parts ( () or [] )
    for match in BRACKET_PATTERN.finditer(full_title):
        content = match.group(0)[1:-1]  # remove () or []
        if VERSION_KEYWORDS.search(content):
            version = content
            title = title.replace(match.group(0), "").strip()
            break

    # --- Step 2: dash-based versions  " - Sub Focus Remix"
    # if not version:
    dash_match = DASH_VERSION_PATTERN.search(title)
    if dash_match:
        candidate = dash_match.group(1)
        if VERSION_KEYWORDS.search(candidate):
            version = candidate
            title = title[:dash_match.start()].strip()

    # --- Cleanup spacing
    title = re.sub(r"\s{2,}", " ", title).strip()
    version = version.strip()

    return title, version


def check_for_vip(title: str) -> bool:
    """ Check if "VIP" is in the title as a version indicator. """
    vip_match = re.search(r"\bVIP\b", title, re.IGNORECASE)
    return vip_match is not None


def extract_version_artist(version: str) -> str:
    """ Extract the version artist from a version string. E.g "Sub Focus Remix" → "Sub Focus" """
    match = re.match(r"^(.*?)\s+(remix|rmx|bootleg|edit|vip|dub|mix|cut|version|rework)$", version, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""
