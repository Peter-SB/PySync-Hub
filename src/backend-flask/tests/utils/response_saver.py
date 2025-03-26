import hashlib
import json
import os

import requests

from app.services.platform_services.soundcloud_service import SoundcloudService, PlaylistNotFoundException


def _resolve_playlist_save_response(playlist_url: str, save_directory: str = "./captured_requests") -> dict:
    """

    """
    playlist_response =SoundcloudService._resolve_playlist(playlist_url)

    # Create the directory if it doesn't exist
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Generate a unique filename using MD5 hash of the URL
    url_hash = hashlib.md5(playlist_url.encode("utf-8")).hexdigest()
    filename = f"playlist_{url_hash}.json"
    file_path = os.path.join(save_directory, filename)

    try:
        with open(file_path, 'w') as f:
            json.dump(playlist_response, f, indent=2)
        print("Saved response JSON to: %s", file_path)
    except Exception as e:
        print("Error saving response JSON to file: %s", e)

    return playlist_response

def _make_http_get_request_save_response(url: str, headers: dict,
                                         save_directory: str = "./captured_requests") -> dict:
    """
       Makes an HTTP GET request to the specified URL with the given headers,
       captures the JSON response, and saves it as a .json file.

       The filename is generated using an MD5 hash of the URL.

       :param url: URL to make the GET request to.
       :param headers: Headers to include in the GET request.
       :param save_directory: Directory where the JSON response will be saved.
                              Defaults to "./captured_requests".
       :return: The JSON response as a dictionary.
       :raises PlaylistNotFoundException: If the GET request returns a 404 status code.
       :raises Exception: For any other non-200 status code.
       """
    print("Making GET request to: %s", url)
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("HTTP GET error for URL %s: %s", url, response.text)
        if response.status_code == 404:
            raise PlaylistNotFoundException("Playlist not found. Could it be private or deleted?", 404)
        raise Exception(f"HTTP GET error: {response.status_code}")

    response_json = response.json()

    # Create the directory if it doesn't exist
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Generate a unique filename using MD5 hash of the URL
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    filename = f"request_{url_hash}.json"
    file_path = os.path.join(save_directory, filename)

    try:
        with open(file_path, 'w') as f:
            json.dump(response_json, f, indent=2)
        print("Saved response JSON to: %s", file_path)
    except Exception as e:
        print("Error saving response JSON to file: %s", e)

    return response_json