import os
import time

import requests
import logging

from app import db
from app.models import Track

logger = logging.getLogger(__name__)

class SoundcloudService:
    @staticmethod
    def _make_http_get_request(url: str, headers: dict) -> dict:
        """
        Helper method for making HTTP GET requests with error handling.
        """
        logger.info("Making GET request to: %s", url)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error("HTTP GET error for URL %s: %s", url, response.text)
            raise Exception(f"HTTP GET error: {response.status_code}")
        return response.json()

    @staticmethod
    def _parse_track(track: dict) -> dict:
        """
        Parses a single track's data from the SoundCloud API into db format.
        """
        if permalink := track.get('permalink_url'):
            error = None
        else:
            error = "No Permalink Found"

        return {
            'platform_id': str(track.get('id')),
            'platform': 'soundcloud',
            'name': track.get('title'),
            'artist': track.get('user', {}).get('username') if track.get('user') else None,
            'album': None,  # SoundCloud tracks typically do not have album info
            'album_art_url': track.get('artwork_url'),
            'download_url': permalink or None,
            'notes_errors': error
        }

    @staticmethod
    def _resolve_playlist(playlist_url: str) -> dict:
        """
        Resolves a SoundCloud playlist URL using the SoundCloud API.
        """
        client_id = os.environ.get('SOUNDCLOUD_CLIENT_ID')
        if not client_id:
            raise ValueError("Missing SoundCloud client ID in environment variables.")

        resolve_url = f"https://api-v2.soundcloud.com/resolve?url={playlist_url}&client_id={client_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/132.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }
        logger.info("Resolving playlist URL: %s", resolve_url)
        return SoundcloudService._make_http_get_request(resolve_url, headers)

    @staticmethod
    def get_playlist_data(playlist_url: str) -> dict:
        """
        Retrieve playlist data from SoundCloud
        """
        try:
            data = SoundcloudService._resolve_playlist(playlist_url)
            image_url = data.get('artwork_url')
            if not image_url and data.get('tracks'):
                first_track = data.get('tracks')[0]
                image_url = first_track.get('artwork_url')

            playlist_data = {
                'name': data.get('title'),
                'external_id': str(data.get('id')),
                'image_url': image_url,
                'track_count': data.get('track_count'),
                'url': data.get('permalink_url')
            }
            return playlist_data
        except Exception as e:
            logger.error("Error fetching SoundCloud playlist data: %s", e, exc_info=True)
            raise e

    @staticmethod
    def get_playlist_tracks(playlist_url: str) -> list:
        """
        Fetches the tracks for a given SoundCloud playlist.
        Returns a list of dictionaries containing track information.
        """
        try:
            data = SoundcloudService._resolve_playlist(playlist_url)
            # Extract track IDs from the resolved playlist data
            track_ids = [track.get('id') for track in data.get('tracks', [])]
            
            # Check for existing tracks in the database
            existing_track_ids = db.session.query(Track.platform_id).filter(
                Track.platform == 'soundcloud',
                Track.platform_id.in_(track_ids)
            ).all()
            existing_track_ids = {track_id[0] for track_id in existing_track_ids}

            # Filter out existing track IDs
            new_track_ids = [track_id for track_id in track_ids if track_id not in existing_track_ids]

            tracks_metadata = []
            client_id = os.environ.get('SOUNDCLOUD_CLIENT_ID')
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/132.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }

            # Iterate over new_track_ids in batches of 20
            for i in range(0, len(new_track_ids), 20):
                batch_ids = new_track_ids[i:i+20]
                batch_ids_str = ','.join(str(x) for x in batch_ids)
                url = f"https://api-v2.soundcloud.com/tracks?ids={batch_ids_str}&client_id={client_id}"
                logger.info("Fetching track metadata for batch: %s", batch_ids_str)
                batch_data = SoundcloudService._make_http_get_request(url, headers)
                tracks_metadata.extend(batch_data)
                time.sleep(0.1)  # To not spam requests

            tracks_data = [SoundcloudService._parse_track(track) for track in tracks_metadata]
            logger.info("Fetched %d tracks for SoundCloud playlist", len(tracks_data))
            return tracks_data
        except Exception as e:
            logger.error("Error fetching SoundCloud playlist tracks: %s", e, exc_info=True)
            raise e

