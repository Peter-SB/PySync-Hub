import pytest
from spotipy import SpotifyException

from app.models import Playlist
from app.repositories.playlist_repository import PlaylistRepository
from tests.mocks.mock_data_helper import MockPlaylistDataHelper


@pytest.mark.usefixtures("client", "init_database")
class TestGetPlaylists():
    """Tests for the GET /api/playlists endpoint."""

    def test_get_playlists_empty(self, client):
        response = client.get('/api/playlists')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_playlists_items(self, client, init_database):
        from app.extensions import db

        playlists = [
            Playlist(name="Chill Vibes", platform="spotify", external_id="12345",
                     image_url="http://example.com/image1.jpg",
                     track_count=10),
            Playlist(name="Workout Mix", platform="soundcloud", external_id="67890",
                     image_url="http://example.com/image2.jpg", track_count=15),
            Playlist(name="Road Trip", platform="spotify", external_id="abcde",
                     image_url="http://example.com/image3.jpg",
                     track_count=8)
        ]

        db.session.bulk_save_objects(playlists)
        db.session.commit()

        response = client.get('/api/playlists')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 3

        names = {playlist.get("name") for playlist in data}
        assert names == {"Chill Vibes", "Workout Mix", "Road Trip"}

    def test_get_full_playlist(self, client, init_database):
        MockPlaylistDataHelper.load_data("Test Playlist 1")

        response = client.get('/api/playlists')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 1

        playlist = data[0]
        assert playlist["name"] == "Test Playlist 1"
        assert playlist["platform"] == "spotify"

    def test_get_playlists_error(self, client, monkeypatch):
        def fake_get_all_playlists():
            raise Exception("Simulated error")

        monkeypatch.setattr(PlaylistRepository, "get_all_playlists", fake_get_all_playlists)

        response = client.get('/api/playlists')
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert "Simulated error" in data["error"]

@pytest.mark.usefixtures("client", "init_database")
class TestGetPlaylistTracks():
    def test_get_playlist_tracks(self, client, init_database):
        MockPlaylistDataHelper.load_data("Test Playlist 1")

        response = client.get('/api/playlist/1/tracks')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 2

        assert data[0]["name"] == "Song One"
        assert data[0]["artist"] == "Artist One"
        assert data[0]["platform"] == "spotify"


@pytest.mark.usefixtures("init_database")
class TestAddPlaylist:
    """
    Tests for the POST /api/playlists endpoint.

    *Takes only spotify or soundcloud playlist URLs. no longer takes IDs

    Tests Include:
    - Adding a playlist with a valid URL - spotify
    - Adding a playlist with a valid URL - soundcloud
    - When playlist is already added
    - When an error
    - Adding a playlist with an invalid URL
    - Adding a playlist id
    """

    def test_add_playlist_valid_spotify(self, client, monkeypatch):
        response = client.post('/api/playlists',
                               json={"url_or_id": "https://open.spotify.com/playlist/3bL14BgPXekKHep3RRdwGZ"})

        assert response.status_code == 201
        playlists = response.get_json()

        assert any(p["external_id"] == "3bL14BgPXekKHep3RRdwGZ" for p in playlists)
        added_playlist = Playlist.query.filter_by(external_id="3bL14BgPXekKHep3RRdwGZ").first()
        assert added_playlist.name == "Test Playlist 1"
        assert added_playlist.track_count == 2
        assert added_playlist.platform == "spotify"

        MockPlaylistDataHelper.save_data(added_playlist)

    def test_add_playlist_valid_soundcloud(self, client, monkeypatch):
        response = client.post('/api/playlists', json={"url_or_id": "https://soundcloud.com/schmoot-point/sets/omwhp"})

        assert response.status_code == 201
        playlists = response.get_json()

        assert any(p["external_id"] == "1890498842" for p in playlists)
        added_playlist = Playlist.query.filter_by(external_id="1890498842").first()
        assert added_playlist.name == "OMWHP"
        assert added_playlist.track_count == 14
        assert added_playlist.platform == "soundcloud"

        assert len(added_playlist.tracks) == 14

    def test_add_playlist_soundcloud_likes(self, client, monkeypatch):
        response = client.post('/api/playlists', json={"url_or_id": "https://soundcloud.com/subfocus/likes"})

        assert response.status_code == 201
        playlists = response.get_json()

        assert any(p["external_id"] == "2121716" for p in playlists)
        added_playlist = Playlist.query.filter_by(external_id="2121716").first()
        assert added_playlist.name == "Likes by Sub Focus"
        assert added_playlist.track_count == 49
        assert added_playlist.platform == "soundcloud"

        assert len(added_playlist.tracks) == 10  # Only 10 tracks are added in test data

    def test_add_playlist_already_added_spotify(self, client, monkeypatch):
        response1 = client.post('/api/playlists',
                                json={"url_or_id": "https://open.spotify.com/playlist/3bL14BgPXekKHep3RRdwGZ"})
        assert response1.status_code == 201

        response2 = client.post('/api/playlists',
                                json={"url_or_id": "https://open.spotify.com/playlist/3bL14BgPXekKHep3RRdwGZ"})
        assert response2.status_code == 400
        error_message = response2.get_json().get("error")
        assert error_message == "Playlist Already Added"

    def test_add_playlist_already_added_soundcloud(self, client, monkeypatch):
        response1 = client.post('/api/playlists', json={"url_or_id": "https://soundcloud.com/schmoot-point/sets/omwhp"})
        assert response1.status_code == 201

        response2 = client.post('/api/playlists', json={"url_or_id": "https://soundcloud.com/schmoot-point/sets/omwhp"})
        assert response2.status_code == 400
        error_message = response2.get_json().get("error")
        assert error_message == "Playlist Already Added"

    def test_add_playlist_not_error_spotify(self, client, monkeypatch):
        response = client.post('/api/playlists', json={"url_or_id": "https://open.spotify.com/playlist/error"})
        assert response.status_code == 400
        error_message = response.get_json().get("error")

        assert error_message == ("Playlist not found. Please check the playlist is public or try another URL.")

    def test_add_playlist_invalid_url(self, client, monkeypatch):
        response = client.post('/api/playlists', json={"url_or_id": "invalid-url"})

        assert response.status_code == 400
        error_message = response.get_json().get("error")
        assert error_message == "Error Adding Playlist: URL Doesnt Look Right. Please try again with a valid URL."

    def test_add_playlist_id(self, client, monkeypatch):
        response = client.post('/api/playlists', json={"url_or_id": "12345"})
        assert response.status_code == 400
        error_message = response.get_json().get("error")
        assert error_message == "Error Adding Playlist: URL Doesnt Look Right. Please try again with a valid URL."
