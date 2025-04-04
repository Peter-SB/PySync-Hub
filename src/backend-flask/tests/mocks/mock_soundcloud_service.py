import hashlib
import json
import os
import logging

from app.services.platform_services.soundcloud_service import SoundcloudService, PlaylistNotFoundException

current_dir = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger(__name__)


class MockSoundcloudService(SoundcloudService):
    """ Mock Spotify Client overrides the _make_http_get_request and _resolve_playlist methods and returns saved
    response objects for seamless unit testing. """

    @staticmethod
    def return_data_from_mock_file(filename: str):
        file_path = os.path.join(current_dir, "../mock_data", filename)
        if os.path.exists(file_path):
            print(f"Soundcloud Playlist Response Mock Data Found: {filename}")
            with open(file_path, 'r', encoding='utf-8') as file:
                return str(file.read())

        raise Exception(f"Mock data file not found : {filename}")

    @staticmethod
    def _make_http_get_request(url: str, headers: dict, query_params=None) -> dict:
        """
        Dummy Soundcloud _make_http_get_request method
        This overrides the HTTP GET request and returns saved response data.
        If url has "error", raise PlaylistNotFoundException
        """
        logger.info("DummySoundcloudService intercepted a http GET request to: %s", url)

        # Simulate an error condition if "error" is in the URL
        if "error" in url:
            logger.error("Simulated error for URL: %s", url)
            raise PlaylistNotFoundException("Playlist not found. Could it be private or deleted?", 404)

        if "tracks?ids=" in url:
            url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()  # Has the url for a short unique filename
            file_path = os.path.join(current_dir, "../mock_data", f"soundcloud_request_{url_hash}.json")
            return json.loads(MockSoundcloudService.return_data_from_mock_file(file_path))

        if "likes" in url:
            user_id = url.rstrip("/").split("/")[-2]
            file_path = os.path.join(current_dir, "../mock_data", f"soundcloud_likes_{user_id}.json")
            return json.loads(MockSoundcloudService.return_data_from_mock_file(file_path))

        raise Exception(f"Mock data not found for request: {url}")

    @staticmethod
    def _make_html_get_request(url: str, headers: dict, query_params=None) -> str:
        """
        Dummy Soundcloud _resolve_playlist method
        If playlist_id is "error" raise PlaylistNotFoundException
        Else return mock data from file with playlist_id
        """
        logger.info("DummySoundcloudService intercepted a HTML GET request to: %s", url)

        if "error" in url:
            raise PlaylistNotFoundException("Playlist not found. Could it be private or deleted?", 404)

        if "sets" in url:
            playlist_name = url.rstrip("/").split("/")[-1]
            file_path = os.path.join(current_dir, "../mock_data", f"soundcloud_playlist_{playlist_name}.txt")
            return MockSoundcloudService.return_data_from_mock_file(file_path)

        # User profile
        user_name = url.rstrip("/").split("/")[-2]
        file_path = os.path.join(current_dir, "../mock_data", f"soundcloud_user_{user_name}.txt")
        return MockSoundcloudService.return_data_from_mock_file(file_path)

    # @staticmethod
    # def _resolve_playlist(playlist_url: str) -> dict:
    #     """
    #     Dummy Soundcloud _resolve_playlist method
    #     If playlist_id is "error" raise PlaylistNotFoundException
    #     Else return mock data from file with playlist_id
    #     """
    #     if playlist_url == "error":
    #         raise PlaylistNotFoundException("Playlist not found. Could it be private or deleted?", 404)
    #
    #     playlist_id = playlist_url.rstrip("/").split("/")[-1]
    #     file_path = os.path.join(current_dir, "../mock_data", f"soundcloud_playlist_{playlist_id}.json")
    #     if os.path.exists(file_path):
    #         print(f"Soundcloud Playlist Response Mock Data Found: soundcloud_playlist_{playlist_id}.json")
    #         with open(file_path, 'r') as file:
    #             return json.load(file)
    #
    #     raise Exception(f"Mock playlist data not found for playlist_id: {playlist_id}")
