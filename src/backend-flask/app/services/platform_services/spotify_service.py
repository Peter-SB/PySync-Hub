import logging
from datetime import datetime
from urllib import request

from flask import session, redirect, url_for
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from app.repositories.playlist_repository import PlaylistRepository
from config import Config

logger = logging.getLogger(__name__)

SPOTIPY_CALLBACK_URL = f'http://localhost:{Config.SPOTIFY_PORT_NUMBER}/callback'

class SpotifyService:
    @staticmethod
    def get_client():
        return Spotify(auth_manager=SpotifyClientCredentials(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET
        ))

    @staticmethod
    def get_auth_client():
        auth_manager = SpotifyOAuth(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_CALLBACK_URL,
            scope=Config.SPOTIFY_OAUTH_SCOPE,
            cache_path=Config.SPOTIFY_TOKEN_CACHE
        )

        token_info = auth_manager.get_cached_token()
        if not token_info or auth_manager.is_token_expired(token_info):
            logger.warning("Authentication Error: Please login to Spotify (In Settings).")
        return Spotify(auth_manager=auth_manager)

    @staticmethod
    def get_playlist_data(url: str):
        try:
            if "collection/tracks" in url:
                return SpotifyService._get_saved_tracks_playlist()

            playlist_id = SpotifyService._extract_playlist_id(url)

            client = SpotifyService.get_client()
            response = client.playlist(playlist_id)

            logger.debug(response.get('tracks', []))

            data = {
                'name': response['name'],
                'external_id': playlist_id,
                'image_url': next(iter(response.get('images', [])), {}).get('url'),
                'track_count': response.get('tracks', {}).get("total", "0"),
                'url': response.get("external_urls", {}).get("spotify", ""),
                'platform': 'spotify'
            }

            return data

        except Exception as e:
            raise e

    @staticmethod
    def _get_saved_tracks_playlist():
        """ Create a playlist that will represent the user's liked tracks. """
        client = SpotifyService.get_auth_client()
        response = client.current_user_saved_tracks()

        data = {
            'name': "Your Liked Spotify Songs",
            'external_id': "liked-songs",
            'image_url': "https://misc.scdn.co/liked-songs/liked-songs-300.jpg",
            'track_count': response.get('total', 0),
            'url': "https://open.spotify.com/collection/tracks",
            'platform': 'spotify'
        }

        return data


    @staticmethod
    def get_playlist_tracks(url):
        """
        Fetches the tracks for a given Spotify playlist.
        Returns a list of dictionaries with track information.
        """
        try:
            logger.info("Fetching tracks for playlist %s", url)
            if "collection/tracks" in url:
                return SpotifyService._get_saved_tracks()

            playlist_id = SpotifyService._extract_playlist_id(url)
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
                        continue  # Skip items that aren't valid tracks (e.g. episodes, missing tracks)

                    track_data = SpotifyService._format_track_data(track)
                    tracks_data.append(track_data)

                # Check if there are more pages to fetch. "URL to the next page of items. (null if none)"
                if results.get('next'):
                    offset += limit
                else:
                    break

            logger.info("Fetched %d tracks for playlist %s", len(tracks_data), playlist_id)
            return tracks_data

        except Exception as e:
            logger.error("Error fetching tracks for playlist %s: %s", url, e, exc_info=True)
            raise e

    @staticmethod
    def _get_saved_tracks():
        """
        Retrieves the current user's liked tracks (saved tracks) using SpotifyOAuth.
        It accumulates the tracks page by page while applying a date limit and a track count limit.

        :return: A list of dictionaries, each representing a liked track.
        """
        client = SpotifyService.get_auth_client()

        liked_playlist = PlaylistRepository.get_playlist_by_url("https://open.spotify.com/collection/tracks")
        track_limit = liked_playlist.to_dict().get('track_limit', None)
        date_limit = liked_playlist.to_dict().get('date_limit', "01-01-24")

        liked_songs = []
        try:
            results = client.current_user_saved_tracks()

            while results:
                for item in results["items"]:
                    if not SpotifyService._is_track_within_date_and_track_limit(liked_songs, item, track_limit, date_limit):
                        return liked_songs[:track_limit]

                    track = item.get('track')
                    if not track or track.get('id') is None:
                        return  # Skip items that aren't valid tracks (e.g., episodes, missing tracks)

                    track_data = SpotifyService._format_track_data(track)
                    liked_songs.append(track_data)

                results = client.next(results) if results.get('next') else None
            return liked_songs[:track_limit]
        except Exception as e:
            logger.error("Error retrieving liked tracks: %s", e)
            return []

    @staticmethod
    def _is_track_within_date_and_track_limit(liked_songs, track, track_limit, date_limit) -> bool:
        """
        Checks if the track should be included based on a date limit and track limit.

        :param liked_songs: List of liked songs.
        :param track: Track data.
        """
        # If a date limit is specified, compare the track's added_at date.
        if date_limit is not None:
            try:
                liked_songs_date_limit = datetime.strptime(date_limit, '%d-%m-%y').date()
                track_added_date = datetime.fromisoformat(track["added_at"].replace('Z', '+00:00')).date()
                if track_added_date < liked_songs_date_limit:
                    return False
            except Exception as e:
                logger.error("Error parsing track dates: %s", e)

        if track_limit is not None:
            return len(liked_songs) <= track_limit

        return True

    @staticmethod
    def _extract_playlist_id(url: str) -> str:
        if 'open.spotify.com/playlist/' in url:
            playlist_id = url.split('/')[-1].split('?')[0]
        else:
            playlist_id = url
        return playlist_id

    @classmethod
    def _format_track_data(cls, track, added_at=None):
        return {
            'platform_id': track['id'],
            'platform': 'spotify',
            'name': track['name'],
            'artist': ", ".join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'] if track.get('album') else None,
            'album_art_url': track['album']['images'][0]['url']
            if track.get('album') and track['album'].get('images') else None,
            'download_url': None,  # Can be populated later
            'added_at': added_at,  # When the track was added to the playlist
        }
