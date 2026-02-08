"""
Base interface for all platform services.

This abstract base class defines the standard interface that all platform services
(SoundCloud, YouTube, Spotify, etc.) must implement to ensure consistency across
different music platforms.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BasePlatformService(ABC):
    """
    Abstract base class for platform services.
    
    All platform-specific services (SoundCloud, YouTube, Spotify, etc.) should inherit
    from this class and implement its abstract methods to provide a consistent interface
    for fetching playlist data and tracks.
    """

    @staticmethod
    @abstractmethod
    def get_playlist_data(url: str) -> Dict[str, Any]:
        """
        Fetches metadata for a playlist.
        
        :param url: Platform-specific playlist URL
        :return: Dictionary containing playlist metadata with the following structure:
            {
                'name': str,              # Playlist name/title
                'external_id': str,       # Platform-specific playlist ID
                'image_url': str,         # URL to playlist cover image
                'track_count': int,       # Number of tracks in the playlist
                'url': str,               # Canonical playlist URL
                'platform': str           # Platform identifier (e.g., 'soundcloud', 'spotify', 'youtube')
            }
        :raises Exception: If playlist cannot be fetched or is invalid
        """
        pass

    @staticmethod
    @abstractmethod
    def get_playlist_tracks(url: str) -> List[Dict[str, Any]]:
        """
        Fetches the tracks for a given playlist.
        
        :param url: Platform-specific playlist URL
        :return: List of track dictionaries with the following structure:
            [
                {
                    'platform_id': str,        # Platform-specific track ID
                    'platform': str,           # Platform identifier (e.g., 'soundcloud', 'spotify', 'youtube')
                    'name': str,               # Track name/title
                    'artist': str,             # Artist name(s)
                    'album': str | None,       # Album name (if available)
                    'album_art_url': str | None,  # URL to album art
                    'download_url': str | None,   # Download/stream URL (if available)
                    'notes_errors': str | None,   # Any errors or notes about the track
                    'added_on': str | None,       # Date track was added to playlist (if available)
                },
                ...
            ]
        :raises Exception: If playlist tracks cannot be fetched
        """
        pass


    @staticmethod
    @abstractmethod
    def search_track(query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Searches for tracks on the platform based on a query string.
        
        :param query: Search query string
        :param limit: Maximum number of results to return (default 3)
        :return: List of track dictionaries with the same structure as in get_playlist_tracks
        :return: List of track dictionaries with the following structure:
            [
                {
                    'platform_id': str,        # Platform-specific track ID
                    'platform': str,           # Platform identifier (e.g., 'soundcloud', 'spotify', 'youtube')
                    'name': str,               # Track name/title
                    'artist': str,             # Artist name(s)
                    'album': str | None,       # Album name (if available)
                    'album_art_url': str | None,  # URL to album art
                    'download_url': str | None,   # Download/stream URL (if available)
                    'notes_errors': str | None,   # Any errors or notes about the track
                    'added_on': str | None,       # Date track was added to playlist (if available)
                },
                ...
            ]
        :raises Exception: If search fails
        """
        pass
