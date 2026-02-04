import logging
from datetime import datetime
from typing import List, Dict, Any

from flask import session, redirect, url_for
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from app.repositories.playlist_repository import PlaylistRepository
from app.services.platform_services.spotify_base_service import BaseSpotifyService
from config import Config

logger = logging.getLogger(__name__)

SPOTIPY_CALLBACK_URL = f'http://localhost:{Config.SPOTIFY_PORT_NUMBER}/callback'


class SpotifyApiService(BaseSpotifyService):
    """Spotify service using official Spotify API (requires API keys)."""

    @staticmethod
    def get_client():
        return Spotify(auth_manager=SpotifyClientCredentials(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET
        ))

    @staticmethod
    def get_auth_client(redirect_uri=None) -> Spotify:
        auth_manager = SpotifyOAuth(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=redirect_uri or SPOTIPY_CALLBACK_URL,
            scope=Config.SPOTIFY_OAUTH_SCOPE,
            cache_path=Config.SPOTIFY_TOKEN_CACHE
        )

        token_info = auth_manager.get_cached_token()
        if not token_info or auth_manager.is_token_expired(token_info):
            logger.warning("Authentication Error: Please login to Spotify (In Settings).")
        return Spotify(auth_manager=auth_manager)

    @staticmethod
    def get_playlist_data(url: str) -> Dict[str, Any]:
        try:
            if "collection/tracks" in url:
                return SpotifyApiService._get_saved_tracks_playlist()

            playlist_id = SpotifyApiService._extract_playlist_id(url)

            client = SpotifyApiService.get_client()
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
        client = SpotifyApiService.get_auth_client()
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
    def get_playlist_tracks(url: str) -> List[Dict[str, Any]]:
        """
        Fetches the tracks for a given Spotify playlist.
        Returns a list of dictionaries with track information.
        """
        try:
            logger.info("Fetching tracks for playlist %s", url)
            if "collection/tracks" in url:
                return SpotifyApiService._get_saved_tracks()

            playlist_id = SpotifyApiService._extract_playlist_id(url)
            client = SpotifyApiService.get_client()

            playlist = PlaylistRepository.get_playlist_by_url(url)
            track_limit = playlist.to_dict().get('track_limit', None)
            date_limit = playlist.to_dict().get('date_limit', None)

            tracks_data = []
            limit = 25
            offset = 0

            while True:
                # Fetch a batch of playlist items (tracks)
                results = client.playlist_items(playlist_id, limit=limit, offset=offset)

                for item in results.get('items', []):
                    if not SpotifyApiService._is_track_within_date_and_track_limit(len(tracks_data), item, track_limit,
                                                                                date_limit):
                        return tracks_data[:track_limit]
                    track_added_on = item.get('added_at', None)
                    track = item.get('track')
                    if not track or track.get('id') is None:
                        continue  # Skip items that aren't valid tracks (e.g. episodes, missing tracks)

                    track_data = SpotifyApiService._format_track_data(track, track_added_on)
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
        client = SpotifyApiService.get_auth_client()

        liked_playlist = PlaylistRepository.get_playlist_by_url("https://open.spotify.com/collection/tracks")
        track_limit = liked_playlist.to_dict().get('track_limit', None)
        date_limit = liked_playlist.to_dict().get('date_limit', None)

        liked_songs = []
        try:
            results = client.current_user_saved_tracks()

            while results:
                for item in results["items"]:

                    if not SpotifyApiService._is_track_within_date_and_track_limit(liked_songs, item, track_limit,
                                                                                date_limit):
                        return liked_songs[:track_limit]

                    track = item.get('track')
                    track_added_on = item.get('added_at', None)
                    if not track or track.get('id') is None:
                        continue  # Skip items that aren't valid tracks (e.g., episodes, missing tracks)

                    track_data = SpotifyApiService._format_track_data(track, track_added_on)
                    liked_songs.append(track_data)

                results = client.next(results) if results.get('next') else None
            return liked_songs[:track_limit]
        except Exception as e:
            logger.error("Error retrieving liked tracks: %s", e)
            return []


    @staticmethod
    def search_track(query: str, limit: int = 3) -> list[dict]:
        """ 
        Search for track on Spotify with api by query string. 
        
        :param query: Search query (e.g., "Artist - Title - Version")
        :param limit: Maximum number of results to return (default 3)
        :return: List of track dictionaries
        """
        try:
            client = SpotifyApiService.get_client()
            results = client.search(q=query, type='track', limit=limit)
            
            if not results or 'tracks' not in results:
                logger.warning("No search results found for query: %s", query)
                return []
            
            tracks = results['tracks']['items']
            return [SpotifyApiService._format_track_data(track) for track in tracks]
            
        except Exception as e:
            logger.error("Error searching Spotify for query '%s': %s", query, e, exc_info=True)
            raise