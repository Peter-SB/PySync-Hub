import logging

from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import os

logger = logging.getLogger(__name__)

class SpotifyService:

    @staticmethod
    def get_client():
        return Spotify(auth_manager=SpotifyClientCredentials(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
        ))

    @staticmethod
    def get_playlist_data(url_or_id):
        try:
            client = SpotifyService.get_client()

            if 'open.spotify.com/playlist/' in url_or_id:
                playlist_id = url_or_id.split('/')[-1].split('?')[0]
            else:
                playlist_id = url_or_id

            response = client.playlist(playlist_id)

            data = {
                'name': response['name'],
                'external_id': playlist_id,
                'image_url': response['images'][0]['url'],
                'track_count': len(response.get('tracks', []))
            }
            logger.info(f"{data}")

            return data

        except Exception as e:
            raise e
