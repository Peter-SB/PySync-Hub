import logging

from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import os

from config import Config

logger = logging.getLogger(__name__)


class SpotifyService:
    @staticmethod
    def get_client():
        return Spotify(auth_manager=SpotifyClientCredentials(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET
        ))

    @staticmethod
    def get_playlist_data(url_or_id):
        try:
            playlist_id = SpotifyService._extract_playlist_id(url_or_id)

            client = SpotifyService.get_client()
            response = client.playlist(playlist_id)

            logger.debug(response.get('tracks', []))

            data = {
                'name': response['name'],
                'external_id': playlist_id,
                'image_url': next(iter(response.get('images', [])), {}).get('url'),
                'track_count': response.get('tracks', {}).get("total", "0"),
                'url': response.get("external_urls", {}).get("spotify", "")
            }

            return data

        except Exception as e:
            raise e


    @staticmethod
    def get_playlist_tracks(url_or_id):
        """
        Fetches the tracks for a given Spotify playlist.
        Returns a list of dictionaries with track information.
        """
        try:
            playlist_id = SpotifyService._extract_playlist_id(url_or_id)
            client = SpotifyService.get_client()

            tracks_data = []
            limit = 100
            offset = 0

            while True:
                # Fetch a batch of playlist items (tracks)
                results = client.playlist_items(playlist_id, limit=limit, offset=offset)

                for item in results.get('items', []):
                    track = item.get('track')
                    if not track or track.get('id') is None:
                        continue  # Skip items that aren't valid tracks (e.g., episodes, missing tracks)

                    track_data = {
                        'platform_id': track['id'],
                        'platform': 'spotify',
                        'name': track['name'],
                        'artist': ", ".join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'] if track.get('album') else None,
                        'album_art_url': track['album']['images'][0]['url']
                        if track.get('album') and track['album'].get('images') else None,
                        'download_url': None,  # Can be populated later
                    }
                    tracks_data.append(track_data)

                # Check if there are more pages to fetch. "URL to the next page of items. (null if none)"
                if results.get('next'):
                    offset += limit
                else:
                    break

            logger.info("Fetched %d tracks for playlist %s", len(tracks_data), playlist_id)
            return tracks_data

        except Exception as e:
            logger.error("Error fetching tracks for playlist %s: %s", url_or_id, e, exc_info=True)
            raise e

    @staticmethod
    def _extract_playlist_id(url_or_id: str) -> str:
        if 'open.spotify.com/playlist/' in url_or_id:
            playlist_id = url_or_id.split('/')[-1].split('?')[0]
        else:
            playlist_id = url_or_id
        return playlist_id
