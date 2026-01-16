import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SetlistImportService:
    @staticmethod
    def parse_setlist(raw_text: str) -> List[Dict[str, str]]:
        """
        Parse a setlist string into artist/track pairs.
        """
        lines = SetlistImportService._split_lines(raw_text)
        parsed_entries: List[Dict[str, str]] = []

        for line in lines:
            entry = SetlistImportService._parse_line(line)
            if entry:
                parsed_entries.append(entry)

        return parsed_entries

    @staticmethod
    def _split_lines(raw_text: str) -> List[str]:
        if not raw_text:
            return []
        return [line.strip() for line in raw_text.splitlines() if line.strip()]

    @staticmethod
    def _parse_line(line: str) -> Optional[Dict[str, str]]:
        cleaned = SetlistImportService._strip_prefix(line)
        if not cleaned:
            return None

        parts = re.split(r"\s*[\-\u2013\u2014]\s*", cleaned, maxsplit=1)
        if len(parts) < 2:
            return None

        artist, track = (part.strip() for part in parts)
        if not artist or not track:
            return None

        return {"artist": artist, "track": track}

    @staticmethod
    def _strip_prefix(line: str) -> str:
        value = line.strip()
        value = re.sub(r"^[\u2022\-\*]\s*", "", value)
        value = re.sub(r"^\[\d{1,2}:\d{2}\]\s*", "", value)
        value = re.sub(r"^\d{1,2}:\d{2}\s*", "", value)
        value = re.sub(r"^[\-\u2013\u2014]\s*", "", value)
        return value.strip()
