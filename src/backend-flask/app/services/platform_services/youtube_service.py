import logging
import re
from typing import Optional

from yt_dlp import YoutubeDL
from app.utils.file_download_utils import FileDownloadUtils

logger = logging.getLogger(__name__)


YDL_OPTIONS = {
    'quiet': True,
    'extract_flat': 'in_playlist', # True,
    'skip_download': True,  
    'force_generic_extractor': False,
    'ignoreerrors': True,  # Skip unavailable videos
    'dump_single_json': True,
}

class YouTubeService:
    """Service for fetching YouTube playlist data and tracks."""

    @staticmethod
    def get_playlist_data(url: str) -> dict:
        """
        Fetches metadata for a YouTube playlist.
        
        :param playlist_url: YouTube playlist URL
        :return: Dictionary containing playlist metadata
        :raises Exception: If playlist cannot be fetched or is invalid
        """
        try:
            playlist_id = YouTubeService._extract_playlist_id(url)
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            

            
            with YoutubeDL(YDL_OPTIONS) as ydl:
                logger.info("Fetching YouTube playlist data for: %s", playlist_url)
                info = ydl.extract_info(playlist_url, download=False)
                
                if not info:
                    raise Exception("Failed to fetch playlist information")
                
                if info.get('_type') != 'playlist':
                    raise Exception("URL is not a valid playlist")
                
                # Get entries count, filtering out unavailable/private videos
                entries = info.get('entries', [])
                available_entries = [e for e in entries if e is not None]
                
                # Handle empty playlists
                if len(available_entries) == 0 and len(entries) == 0:
                    raise Exception("Playlist is empty")
                
                # Get thumbnail - prefer playlist thumbnail, fallback to first video
                image_url = info.get('thumbnails', [{}])[-1].get('url') if info.get('thumbnails') else None
                if not image_url and available_entries:
                    first_entry_thumbnails = available_entries[0].get('thumbnails', [])
                    if first_entry_thumbnails:
                        image_url = first_entry_thumbnails[-1].get('url')
                
                data = {
                    'name': info.get('title', 'YouTube Playlist'),
                    'external_id': playlist_id,
                    'image_url': image_url,
                    'track_count': len(available_entries),
                    'url': playlist_url,
                    'platform': 'youtube'
                }
                
                logger.info("Successfully fetched playlist data: %s tracks", data['track_count'])
                return data
                
        except Exception as e:
            logger.error("Error fetching YouTube playlist data: %s", e, exc_info=True)
            raise e

    @staticmethod
    def get_playlist_tracks(playlist_url: str) -> list[dict]:
        """
        Fetches all tracks from a YouTube playlist.
        
        :param playlist_url: YouTube playlist URL
        :return: List of track dictionaries
        :raises Exception: If tracks cannot be fetched
        """
        try:
            logger.info("Fetching tracks for YouTube playlist: %s", playlist_url)
            
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                
                if not info or info.get('_type') != 'playlist':
                    raise Exception("Invalid playlist")
                
                entries = info.get('entries', [])
                tracks_data = []
                
                for entry in entries:
                    # Skip unavailable or private videos
                    if entry is None:
                        logger.debug("Skipping unavailable video in playlist")
                        continue

                    # Skip if essential data is missing
                    if not entry.get('id'):
                        logger.debug("Skipping entry without ID")
                        continue

                    # Skip deleted/delisted videos
                    if entry.get('title') == '[Deleted video]' or entry.get('title') is None: 
                        logger.debug("Skipping deleted or delisted video in playlist, id: %s", entry.get('id'))
                        continue                    

                    track_data = YouTubeService._format_track_data(entry)
                    track_data["album"] = "" #info.get("title")  # Use playlist title as album
                    tracks_data.append(track_data)
                
                logger.info("Fetched %d tracks from YouTube playlist", len(tracks_data))
                return tracks_data
                
        except Exception as e:
            logger.error("Error fetching YouTube playlist tracks: %s", e, exc_info=True)
            raise e

    @staticmethod
    def _format_track_data(entry: dict) -> dict:
        """
        Formats YouTube video data into track format.
        
        :param entry: YouTube video entry from yt-dlp
        :return: Formatted track dictionary
        """
        # Extract artist and title from video title
        title = entry.get('title', 'Unknown Title')
        artist = entry.get('uploader', 'Unknown Artist')

        # Remove "Free Download" or similar tags from title
        title = FileDownloadUtils.strip_junk_tags_from_title(title)
        
        # Try to parse "Artist - Title" format if present
        if ' - ' in title:
            parts = title.split(' - ', 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        

        # Get the best thumbnail
        thumbnails = entry.get('thumbnails', [])
        album_art_url = thumbnails[-1].get('url') if thumbnails else None
        
        return {
            'platform_id': entry.get('id'),
            'platform': 'youtube',
            'name': title,
            'artist': artist,
            'album': None, 
            'album_art_url': album_art_url,
            'download_url': entry.get('webpage_url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
            'added_on': None,
        }

    @staticmethod
    def _extract_playlist_id(url: str) -> str:
        """
        Extracts the playlist ID from a YouTube URL.
        
        :param url: YouTube playlist URL
        :return: Playlist ID
        :raises ValueError: If URL format is invalid
        """
        # Match various YouTube playlist URL formats
        patterns = [
            r'[?&]list=([a-zA-Z0-9_-]+)', 
            r'youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If URL looks like just a playlist ID
        if re.match(r'^[a-zA-Z0-9_-]+$', url):
            return url
        
        raise ValueError(f"Could not extract playlist ID from URL: {url}")
