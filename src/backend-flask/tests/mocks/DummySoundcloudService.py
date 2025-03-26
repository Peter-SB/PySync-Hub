import hashlib
import json
import os
import time
import logging
from urllib.parse import urlparse, parse_qs

import requests

from app.services.platform_services.soundcloud_service import SoundcloudService, PlaylistNotFoundException

current_dir = os.path.dirname(os.path.abspath(__file__))

class DummySoundcloudService(SoundcloudService):
    """ Dummy Soundcloud Service for testing purposes that overrides _make_http_get_request and returns mock data. """

    @staticmethod
    def _make_http_get_request(url: str, headers: dict) -> dict:
        """
        Dummy implementation that overrides the HTTP GET request.
        It loads local JSON mock data based on the URL instead of making a real request.
        """
        logger = logging.getLogger(__name__)
        logger.info("DummySoundcloudService GET request to: %s", url)

        # Simulate an error condition if "error" is in the URL
        if "error" in url:
            logger.error("Simulated error for URL: %s", url)
            raise PlaylistNotFoundException("Playlist not found. Could it be private or deleted?", 404)

        if "tracks?ids=" in url:
            url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
            filename = f"soundcloud_request_{url_hash}.json"
            file_path = os.path.join(current_dir, "../mock_data", filename)
            if os.path.exists(file_path):
                print(f"Soundcloud Request Response Mock Data Found: {file_path}")
                with open(file_path, 'r', encoding="utf-8") as file:
                    return json.load(file)
            raise Exception(f"Mock data not found Soundcloud Request Response: {file_path}")

        raise Exception(f"Mock data not found for request: {url}")

    @staticmethod
    def _resolve_playlist(playlist_url: str) -> dict:
        """ Dummy Soundcloud resolve_playlist method
        if playlist_id is "error" raise PlaylistNotFoundException
        else return mock data from file with playlist_id
        """
        if playlist_url == "error":
            raise PlaylistNotFoundException("Playlist not found. Could it be private or deleted?", 404)

        playlist_id = playlist_url.rstrip("/").split("/")[-1]
        file_path = os.path.join(current_dir, "../mock_data", f"soundcloud_playlist_{playlist_id}.json")
        if os.path.exists(file_path):
            print(f"Soundcloud Playlist Response Mock Data Found: soundcloud_playlist_{playlist_id}.json")
            with open(file_path, 'r') as file:
                return json.load(file)

        raise Exception(f"Mock data not found for playlist_id: {playlist_id}")
