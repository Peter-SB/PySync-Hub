import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from dateutil.parser import isoparse, parse
from app.services.platform_services.base_platform_service import BasePlatformService

logger = logging.getLogger(__name__)


class BaseSpotifyService(BasePlatformService, ABC):
    """Base class for Spotify services with shared functionality."""

    @staticmethod
    @abstractmethod
    def get_playlist_data(url: str) -> Dict[str, Any]:
        """
        Fetches playlist metadata.
        Must be implemented by subclasses.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_playlist_tracks(url: str) -> List[Dict[str, Any]]:
        """
        Fetches the tracks for a given Spotify playlist.
        Must be implemented by subclasses.
        """
        pass

    @classmethod
    def _format_track_data(cls, track, track_added_on=None):
        """
        Format track data to a standardized format.
        Works with both API and scraper data.
        """
        return {
            'platform_id': track['id'],
            'platform': 'spotify',
            'name': track['name'],
            'artist': ", ".join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'] if track.get('album') else None,
            'album_art_url': track['album']['images'][0]['url']
                if track.get('album') and track['album'].get('images') else None,
            'download_url': None,  # Can be populated later
            'added_on': track_added_on,  # When the track was added to the playlist
            'duration_ms': track.get('duration_ms'),
        }

    @staticmethod
    def _extract_playlist_id(url: str) -> str:
        """Extract playlist ID from Spotify URL."""
        if 'open.spotify.com/playlist/' in url:
            playlist_id = url.split('/')[-1].split('?')[0]
        else:
            playlist_id = url
        return playlist_id

    @staticmethod
    def _extract_track_id(url: str) -> Optional[str]:
        """Extract track ID from Spotify URL or URI."""
        if not url:
            return None
        if url.startswith('spotify:track:'):
            return url.split(':')[-1] or None
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 'track':
            return path_parts[1].split('?')[0] or None
        return None

    @staticmethod
    def _is_track_within_date_and_track_limit(playlist_length: int, track, track_limit, date_limit) -> bool:
        """
        Checks if the track should be included based on a date limit and track limit.

        :param playlist_length: Number of songs already in playlist.
        :param track: Track data.
        """
        # If a date limit is specified, compare the track's added_at date.
        if date_limit is not None:
            try:
                playlist_date_limit = parse(date_limit).date()
                track_added_date = isoparse(track["added_at"]).date()
                if track_added_date < playlist_date_limit:
                    return False
            except Exception as e:
                logger.error("Error parsing track dates: %s", e)

        if track_limit is not None:
            return playlist_length <= track_limit

        return True
