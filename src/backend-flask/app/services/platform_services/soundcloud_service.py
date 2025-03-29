import json
import os
import re
import time

import requests
import logging
from bs4 import BeautifulSoup

from app.models import Track
from app.repositories.playlist_repository import PlaylistRepository
from config import Config

logger = logging.getLogger(__name__)


class PlaylistNotFoundException(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


class SoundcloudService:
    @staticmethod
    def _make_http_get_request(url: str, headers: dict, query_params=None) -> dict:
        """
        Helper method for making HTTP GET requests with error handling.
        """
        logger.info("Making GET request to: %s", url)

        client_id = Config.SOUNDCLOUD_CLIENT_ID
        if not client_id:
            raise ValueError("Missing SoundCloud client ID in environment variables.")

        response = requests.get(url, headers=headers, params=query_params)
        if response.status_code != 200:
            logger.error("HTTP GET error for URL %s: %s", url, response.text)

            if response.status_code == 404:
                raise PlaylistNotFoundException("Playlist not found. Could it be private or deleted?", 404)

            raise Exception(f"HTTP GET error: {response.status_code} {response.text}")

        return response.json()

    @staticmethod
    def _make_html_get_request(url: str, headers: dict, query_params=None) -> str:
        """
        Helper method for making HTTP GET requests with error handling.
        """
        logger.info("Making GET request to: %s", url)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error("HTTP GET error for URL %s: %s", url, response.text)

            if response.status_code == 404:
                raise PlaylistNotFoundException("Playlist not found. Could it be private or deleted?", 404)

            raise Exception(f"HTTP GET error: {response.status_code} {response.text}")

        return response.text

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
    @DeprecationWarning
    def _resolve_playlist_old(playlist_url: str) -> dict:
        """
        Resolves a SoundCloud playlist URL using the SoundCloud API.
        Deprecated by SoundCloud api change.
        """
        client_id = "akcDl6lB9RfwyhLSb2Xw2MwPR3Ow85Kr"  # Config.SOUNDCLOUD_CLIENT_ID
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
    def _resolve_playlist(playlist_url: str) -> dict:
        """
        Resolves a SoundCloud playlist URL using the SoundCloud API.
        Playlist data is stored in a script tag in the HTML of the playlist page.
        """
        response = requests.get(playlist_url, headers=headers)
        if response.status_code != 200:
            raise Exception("Failed to retrieve page")

        # Extract script containing window.__sc_hydration
        soup = BeautifulSoup(response.text, "html.parser")
        script_tags = soup.find_all("script")

        hydration_data = None
        for script in script_tags:
            if "window.__sc_hydration" in script.text:
                match = re.search(r"window\.__sc_hydration\s*=\s*(\[\{.*?\}\]);", script.text, re.DOTALL)
                if match:
                    hydration_data = json.loads(match.group(1))
                    break

        if not hydration_data:
            raise Exception("Playlist data not found")

        # Find the playlist data
        for item in hydration_data:
            if item.get("hydratable") == "playlist":
                return item["data"]  # This contains the playlist information

        raise Exception("No playlist data found")

    @staticmethod
    def _resolve_likes_playlist(playlist_url: str) -> dict:
        """
        Get the liked tracks playlist info.

        Get the liked tracks of a user from soundcloud.
        First get the user id with a request to soundcloud.com/{username}. (get the id from the hydrated script e.g "id":2121716)
        Then get the tracks from api-v2.soundcloud.com/users/{user_id}/likes?client_id={}&limit=25&offset=0
        (if there is a "next_href" key in the response, continue loading are more tracks)
        """
        response = requests.get(playlist_url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve user page. Status code: {response.status_code}")

        # Extract script containing window.__sc_hydration
        soup = BeautifulSoup(response.text, "html.parser")
        script_tags = soup.find_all("script")

        hydration_data = None
        for script in script_tags:
            if "window.__sc_hydration" in script.text:
                match = re.search(r"window\.__sc_hydration\s*=\s*(\[\{.*?\}\]);", script.text, re.DOTALL)
                if match:
                    try:
                        hydration_data = json.loads(match.group(1))
                        break
                    except Exception as e:
                        raise Exception(f"Error parsing hydration soundcloud user id JSON: {e}")

        if not hydration_data:
            raise Exception("User ID data not found")

        user_data = None
        for item in hydration_data:
            if item.get("hydratable") == "user":
                user_data = item["data"]
                break
        if not user_data:
            raise Exception("User data not found in hydration data")

        return {
            'title': f"Likes by {user_data.get('first_name')}",
            'id': user_data.get("id"),
            'artwork_url': user_data.get("avatar_url"),
            'track_count': user_data.get('likes_count'),
            'permalink_url': f"{playlist_url}",
        }

    @staticmethod
    def _resolve_likes_playlist_tracks(playlist_url) -> list[dict]:
        """

        :param playlist_url: url of the liked track playlist used to resolve the playlist from the db
        :return: List of track dictionaries in _parse_track format
        """
        playlist = PlaylistRepository.get_playlist_by_url(playlist_url)
        if not playlist:
            raise Exception(f"Playlist not found in you database for url: {playlist_url}")

        client_id = Config.SOUNDCLOUD_CLIENT_ID

        limit = 25
        liked_tracks = []
        api_url = (f"https://api-v2.soundcloud.com/users/{playlist.external_id}/likes?"
                   f"client_id={client_id}&limit={limit}&offset=0")
        query_params = [("client_id", client_id)]
        while True:
            data = SoundcloudService._make_http_get_request(api_url, headers, query_params)
            if "collection" not in data:
                break

            liked_tracks.extend(data["collection"])

            # If there is no further page, exit the loop.
            if not data.get("collection") or not data.get("next_href"):
                break
            api_url = data.get("next_href")
            time.sleep(0.1)  # be nice to the API
        liked_tracks_formatted = [SoundcloudService._parse_track(track.get("track")) for track in liked_tracks if
                                  track.get("track")]

        return liked_tracks_formatted

    @staticmethod
    def get_playlist_data(playlist_url: str) -> dict:
        """
        Retrieve playlist data from SoundCloud
        """
        try:
            if "likes" in playlist_url:
                data = SoundcloudService._resolve_likes_playlist(playlist_url)
            else:
                data = SoundcloudService._resolve_playlist(playlist_url)

            image_url = data.get('artwork_url')
            # Use the first tracks artwork as fallback if playlist has no image
            if not image_url and data.get('tracks'):
                first_track = data.get('tracks')[0]
                image_url = first_track.get('artwork_url')

            playlist_data = {
                'name': data.get('title'),
                'external_id': str(data.get('id')),
                'image_url': image_url,
                'track_count': data.get('track_count'),
                'url': data.get('permalink_url'),
                'platform': 'soundcloud'
            }
            return playlist_data
        except Exception as e:
            logger.error("Error fetching SoundCloud playlist data: %s", e, exc_info=True)
            raise e

    @staticmethod
    def get_playlist_tracks(playlist_url: str) -> list[dict]:
        """
        Fetches the tracks for a given SoundCloud playlist.
        Returns a list of dictionaries containing track information
        in the order they appear in the SoundCloud playlist.

        :return: List of track dictionaries in _parse_track format

        todo: fix track order by rewriting the exclude existing track logic because thats excluding tacks on other
        playlists. Need to pass all tracks back, just query the db for existing tracks and exclude them from the
        call to the soundcloud api
        """
        try:
            if "likes" in playlist_url:
                return SoundcloudService._resolve_likes_playlist_tracks(playlist_url)
            else:
                data = SoundcloudService._resolve_playlist(playlist_url)
                resolved_tracks = data.get('tracks', [])

            logger.info("Fetched %d tracks for SoundCloud playlist", len(resolved_tracks))

            new_track_ids = [track.get('id') for track in resolved_tracks]

            # todo: add back to reduce redundant calls to the soundcloud api
            # # Get the track IDs in the order from the playlist
            # track_ids = [track.get('id') for track in resolved_tracks]
            #
            # logger.info("Fetched %d track ids for SoundCloud playlist", len(track_ids))
            #
            # # Check for existing tracks in the database
            # existing_track_ids = db.session.query(Track.platform_id).filter(
            #     Track.platform == 'soundcloud',
            #     Track.platform_id.in_([str(tid) for tid in track_ids])
            # ).all()
            # existing_track_ids = {track_id[0] for track_id in existing_track_ids}
            # logger.info("Fetched %d existing track ids for SoundCloud playlist", len(existing_track_ids))
            #
            #
            # # Filter out track IDs that already exist
            # new_track_ids = [tid for tid in track_ids if str(tid) not in existing_track_ids]

            tracks_metadata = []
            client_id = Config.SOUNDCLOUD_CLIENT_ID

            # Fetch metadata in batches to avoid spamming requests
            for i in range(0, len(new_track_ids), 20):
                batch_ids = new_track_ids[i:i + 20]
                batch_ids_str = ','.join(str(x) for x in batch_ids)
                url = f"https://api-v2.soundcloud.com/tracks?ids={batch_ids_str}&client_id={client_id}"
                logger.info("Fetching track metadata for batch: %s", batch_ids_str)
                batch_data = SoundcloudService._make_http_get_request(url, headers)
                tracks_metadata.extend(batch_data)
                time.sleep(0.1)  # Brief pause between requests

            # Parse each track's metadata into our db format
            new_tracks_data = [SoundcloudService._parse_track(track) for track in tracks_metadata]

            # Create a lookup dict for the new tracks using platform_id (as string) as key
            new_tracks_dict = {track['platform_id']: track for track in new_tracks_data}

            # Rebuild the track list in the order as in the original playlist
            ordered_new_tracks = []
            for track in resolved_tracks:
                tid_str = str(track.get('id'))
                if tid_str in new_tracks_dict:
                    ordered_new_tracks.append(new_tracks_dict[tid_str])

            logger.info("Fetched %d new tracks for SoundCloud playlist", len(ordered_new_tracks))
            return ordered_new_tracks
        except Exception as e:
            logger.error("Error fetching SoundCloud playlist tracks: %s", e, exc_info=True)
            raise e
