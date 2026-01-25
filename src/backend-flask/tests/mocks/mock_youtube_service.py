import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MockYouTubeService:
    """Mock YouTube service for testing."""

    @staticmethod
    def get_playlist_data(url: str) -> dict:
        """Mock implementation of get_playlist_data."""
        logger.info("MockYouTubeService.get_playlist_data called with url: %s", url)
        
        # Handle error case
        if "error" in url or "invalid" in url:
            raise Exception("Playlist not found. Please check the playlist is public or try another URL.")
        
        # Handle empty playlist
        if "empty" in url:
            raise Exception("Playlist is empty")
        
        # Valid playlist with unavailable videos
        if "unavailable" in url:
            return {
                'name': 'Test YouTube Playlist with Unavailable Videos',
                'external_id': 'PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j',
                'image_url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
                'track_count': 2,  # Only 2 available out of 3
                'url': url,
                'platform': 'youtube'
            }
        
        # Default valid playlist
        return {
            'name': 'Test YouTube Playlist',
            'external_id': 'PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j',
            'image_url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
            'track_count': 3,
            'url': url,
            'platform': 'youtube'
        }

    @staticmethod
    def get_playlist_tracks(url: str) -> list[dict]:
        """Mock implementation of get_playlist_tracks."""
        logger.info("MockYouTubeService.get_playlist_tracks called with url: %s", url)
        
        # Handle error case
        if "error" in url or "invalid" in url:
            raise Exception("Invalid playlist")
        
        # Handle empty playlist
        if "empty" in url:
            return []
        
        # Playlist with unavailable videos
        if "unavailable" in url:
            return [
                {
                    'platform_id': 'dQw4w9WgXcQ',
                    'platform': 'youtube',
                    'name': 'Never Gonna Give You Up',
                    'artist': 'Rick Astley',
                    'album': None,
                    'album_art_url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
                    'download_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'added_on': None,
                },
                {
                    'platform_id': 'jNQXAC9IVRw',
                    'platform': 'youtube',
                    'name': 'Me at the zoo',
                    'artist': 'jawed',
                    'album': None,
                    'album_art_url': 'https://i.ytimg.com/vi/jNQXAC9IVRw/hqdefault.jpg',
                    'download_url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',
                    'added_on': None,
                }
                # Note: Third video is unavailable/private and not included
            ]
        
        # Default valid playlist
        return [
            {
                'platform_id': 'dQw4w9WgXcQ',
                'platform': 'youtube',
                'name': 'Never Gonna Give You Up',
                'artist': 'Rick Astley',
                'album': None,
                'album_art_url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
                'download_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'added_on': None,
            },
            {
                'platform_id': 'jNQXAC9IVRw',
                'platform': 'youtube',
                'name': 'Me at the zoo',
                'artist': 'jawed',
                'album': None,
                'album_art_url': 'https://i.ytimg.com/vi/jNQXAC9IVRw/hqdefault.jpg',
                'download_url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',
                'added_on': None,
            },
            {
                'platform_id': '9bZkp7q19f0',
                'platform': 'youtube',
                'name': 'PSY - GANGNAM STYLE',
                'artist': 'officialpsy',
                'album': None,
                'album_art_url': 'https://i.ytimg.com/vi/9bZkp7q19f0/hqdefault.jpg',
                'download_url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
                'added_on': None,
            }
        ]

    @staticmethod
    def _extract_playlist_id(url: str) -> str:
        """Mock implementation of _extract_playlist_id."""
        if "list=" in url:
            return url.split("list=")[1].split("&")[0]
        return "PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"
