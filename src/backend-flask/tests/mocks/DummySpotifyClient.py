import pytest
from spotipy import SpotifyException

from app import SpotifyService


class DummySpotifyClient:
    def playlist(self, playlist_id):
        print(playlist_id)
        if playlist_id is "error":
            print("Error")
            raise Exception(http_status=404, msg="Not Found")

        return {
            "name": "Test Playlist",
            "tracks": {"total": 2},
            "images": [{"url": "http://example.com/image.png"}],
            "external_urls": {"spotify": "http://example.com/playlist"},
            "external_id": "123TestId"
        }

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

