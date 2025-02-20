import os
import requests
import logging

logger = logging.getLogger(__name__)

class SoundcloudService:
    @staticmethod
    def _resolve_playlist(playlist_url: str) -> dict:
        """
        Helper method that resolves a SoundCloud playlist URL using the SoundCloud API.
        """
        client_id = os.environ.get('SOUNDCLOUD_CLIENT_ID')
        if not client_id:
            raise ValueError("Missing SoundCloud client ID in environment variables.")

        resolve_url = f"https://api-v2.soundcloud.com/resolve?url={playlist_url}&client_id={client_id}"
        # Mimic a browser's headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/132.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
            # You might need to add additional headers if necessary
        }

        logger.info(f"https://api-v2.soundcloud.com/resolve?url={playlist_url}&client_id={client_id}")
        response = requests.get(resolve_url, headers=headers)

        if response.status_code != 200:
            logger.error("SoundCloud API error for URL %s: %s", playlist_url, response.text)
            raise Exception(f"SoundCloud API error: {response.status_code}")
        return response.json()

    @staticmethod
    def get_playlist_data(playlist_url: str) -> dict:
        """
        Retrieves basic playlist data from SoundCloud.

        Returns a dictionary with:
          - name: The playlist title.
          - external_id: The playlist ID from SoundCloud.
          - image_url: The artwork URL.
          - track_count: The number of tracks in the playlist.
          - url: The permalink URL of the playlist.
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
            tracks = data.get('tracks', [])
            logger.info("%s", tracks)
            return []

            tracks_data = []
            for track in tracks:
                track_data = {
                    'platform_id': str(track.get('id')),
                    'platform': 'soundcloud',
                    'name': track.get('title'),
                    'artist': track.get('user', {}).get('username'),
                    'album': None,  # SoundCloud tracks typically do not have album info
                    'album_art_url': track.get('artwork_url'),
                    'download_url': None,  # Can be populated later if needed
                }
                tracks_data.append(track_data)
            logger.info("Fetched %d tracks for SoundCloud playlist", len(tracks_data))
            return tracks_data
        except Exception as e:
            logger.error("Error fetching SoundCloud playlist tracks: %s", e, exc_info=True)
            raise e
