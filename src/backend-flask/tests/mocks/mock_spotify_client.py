import json
import os

import pytest
from spotipy import SpotifyException

from app import SpotifyService

current_dir = os.path.dirname(os.path.abspath(__file__))

class MockSpotifyClient:
    """ Mock Spotify Client overrides the playlist and playlist_items methods and returns saved response objects
    for seamless unit testing. """

    def playlist(self, playlist_id):
        """ Mock Spotipy Client playlist method
        if playlist_id is "error" raise SpotifyException
        else return mock data from file with playlist_id
        """

        print(f"DummySpotifyClient playlist_id: {playlist_id}")
        if playlist_id == "error":
            print("Playlist Error")
            raise SpotifyException(code=404, http_status=404, msg="Not Found")

        file_path = os.path.join(current_dir, "../mock_data", f"spotipy_playlist_{playlist_id}.json")
        if os.path.exists(file_path):
            print(f"Spotipy Playlist Response Mock Data Found:spotipy_playlist_{playlist_id}.json")
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)

        raise Exception(f"Mock data not found for playlist_id: {playlist_id}")

    def playlist_items(self, playlist_id, limit=100, offset=0):
        return {
            "items": [
                {
                    "track": {
                        "id": "track1",
                        "name": "Song One",
                        "artists": [{"name": "Artist One"}],
                        "album": {
                            "name": "Album One",
                            "images": [{"url": "http://example.com/album1.png"}]
                        }
                    }
                },
                {
                    "track": {
                        "id": "track2",
                        "name": "Song Two",
                        "artists": [{"name": "Artist Two"}],
                        "album": {
                            "name": "Album Two",
                            "images": [{"url": "http://example.com/album2.png"}]
                        }
                    }
                }
            ],
            "next": None
        }

