import pytest
from unittest.mock import MagicMock
from app.services.spotify_service import SpotifyService


@pytest.fixture
def mock_spotify_client():
    """Creates a mock instance of spotipy.Spotify"""
    mock_client = MagicMock()
    mock_client.playlist.return_value = {
        "name": "Test Playlist",
        "images": [{"url": "http://test.com/playlist.jpg"}],
        "tracks": {"total": 10},
        "external_urls": {"spotify": "http://spotify.com/test"},
    }
    mock_client.playlist_items.return_value = {
        "items": [
            {
                "track": {
                    "id": "track1",
                    "name": "Test Track 1",
                    "artists": [{"name": "Artist 1"}],
                    "album": {"name": "Test Album", "images": [{"url": "http://test.com/album.jpg"}]},
                }
            },
            {
                "track": {
                    "id": "track2",
                    "name": "Test Track 2",
                    "artists": [{"name": "Artist 2"}],
                    "album": {"name": "Test Album", "images": [{"url": "http://test.com/album.jpg"}]},
                }
            },
        ],
        "next": None
    }
    return mock_client


@pytest.fixture
def spotify_service(mock_spotify_client, monkeypatch):
    """
    Patch SpotifyService.get_client so it returns the mock_spotify_client.
    Since all SpotifyService methods are static, we don't create an instance;
    we simply return the class after patching.
    """
    monkeypatch.setattr(SpotifyService, "get_client", lambda: mock_spotify_client)
    return SpotifyService


# ======================================================================================================================
# ====================================================TESTS=============================================================
# ======================================================================================================================

def test_get_playlist_data(spotify_service, mock_spotify_client):
    """Test fetching playlist metadata"""
    playlist_url = "https://open.spotify.com/playlist/test123"
    expected_result = {
        "name": "Test Playlist",
        "external_id": "test123",
        "image_url": "http://test.com/playlist.jpg",
        "track_count": 10,
        "url": "http://spotify.com/test"
    }

    result = spotify_service.get_playlist_data(playlist_url)
    assert result == expected_result
    mock_spotify_client.playlist.assert_called_once_with("test123")


def test_get_playlist_data_missing_fields(spotify_service, mock_spotify_client):
    """Test fetching playlist metadata when fields are missing"""
    mock_spotify_client.playlist.return_value = {
        "name": "Incomplete Playlist",
        "images": [],
        "tracks": {},  # Missing 'total'
        "external_urls": {}
    }

    playlist_url = "https://open.spotify.com/playlist/test123"
    expected_result = {
        "name": "Incomplete Playlist",
        "external_id": "test123",
        "image_url": None,  # No images provided
        "track_count": "0",  # Default fallback value
        "url": ""  # No external URL
    }

    result = spotify_service.get_playlist_data(playlist_url)
    assert result == expected_result


def test_get_playlist_tracks(spotify_service, mock_spotify_client):
    """Test fetching playlist tracks"""
    playlist_url = "https://open.spotify.com/playlist/test123"
    expected_tracks = [
        {
            "platform_id": "track1",
            "platform": "spotify",
            "name": "Test Track 1",
            "artist": "Artist 1",
            "album": "Test Album",
            "album_art_url": "http://test.com/album.jpg",
            "download_url": None
        },
        {
            "platform_id": "track2",
            "platform": "spotify",
            "name": "Test Track 2",
            "artist": "Artist 2",
            "album": "Test Album",
            "album_art_url": "http://test.com/album.jpg",
            "download_url": None
        }
    ]

    result = spotify_service.get_playlist_tracks(playlist_url)
    assert result == expected_tracks
    mock_spotify_client.playlist_items.assert_called_once_with("test123", limit=100, offset=0)


def test_get_playlist_tracks_empty(spotify_service, mock_spotify_client):
    """Test fetching playlist tracks when playlist is empty"""
    mock_spotify_client.playlist_items.return_value = {
        "items": [],
        "next": None
    }

    playlist_url = "https://open.spotify.com/playlist/test123"
    result = spotify_service.get_playlist_tracks(playlist_url)

    assert result == []  # Expect an empty list


def test_get_playlist_tracks_pagination(spotify_service, mock_spotify_client):
    """Test fetching playlist tracks when multiple API calls are needed"""
    mock_spotify_client.playlist_items.side_effect = [
        {
            "items": [
                {
                    "track": {
                        "id": "track1",
                        "name": "Track 1",
                        "artists": [{"name": "Artist 1"}],
                        "album": {"name": "Album 1", "images": [{"url": "http://test.com/album1.jpg"}]},
                    }
                }
            ],
            "next": "https://api.spotify.com/v1/next_page",  # More tracks available
        },
        {
            "items": [
                {
                    "track": {
                        "id": "track2",
                        "name": "Track 2",
                        "artists": [{"name": "Artist 2"}],
                        "album": {"name": "Album 2", "images": [{"url": "http://test.com/album2.jpg"}]},
                    }
                }
            ],
            "next": None,  # No more pages
        }
    ]

    playlist_url = "https://open.spotify.com/playlist/test123"
    expected_tracks = [
        {
            "platform_id": "track1",
            "platform": "spotify",
            "name": "Track 1",
            "artist": "Artist 1",
            "album": "Album 1",
            "album_art_url": "http://test.com/album1.jpg",
            "download_url": None
        },
        {
            "platform_id": "track2",
            "platform": "spotify",
            "name": "Track 2",
            "artist": "Artist 2",
            "album": "Album 2",
            "album_art_url": "http://test.com/album2.jpg",
            "download_url": None
        }
    ]

    result = spotify_service.get_playlist_tracks(playlist_url)
    assert result == expected_tracks
    assert mock_spotify_client.playlist_items.call_count == 2  # Ensure pagination occurred


@pytest.mark.parametrize(
    "input_url, expected_id",
    [
        ("https://open.spotify.com/playlist/test123", "test123"),
        ("test123", "test123"),
        ("https://open.spotify.com/playlist/4XOBNqyylYCZTZDCHlqI6z?si=1f13b6eb71c14f17", "4XOBNqyylYCZTZDCHlqI6z"),
        ("", "")
    ]
)
def test_extract_playlist_id(input_url, expected_id):
    """Test extracting playlist ID from various valid and invalid inputs"""
    assert SpotifyService._extract_playlist_id(input_url) == expected_id
