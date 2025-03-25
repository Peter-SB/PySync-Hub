import pytest
from spotipy import SpotifyException

from app.models import Playlist
from app.repositories.playlist_repository import PlaylistRepository

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
            Playlist(name="Chill Vibes", platform="spotify", external_id="12345", image_url="http://example.com/image1.jpg",
                     track_count=10),
            Playlist(name="Workout Mix", platform="soundcloud", external_id="67890",
                     image_url="http://example.com/image2.jpg", track_count=15),
            Playlist(name="Road Trip", platform="spotify", external_id="abcde", image_url="http://example.com/image3.jpg",
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

    def test_get_playlists_error(self, client, monkeypatch):
        def fake_get_all_playlists():
            raise Exception("Simulated error")

        monkeypatch.setattr(PlaylistRepository, "get_all_playlists", fake_get_all_playlists)

        response = client.get('/api/playlists')
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert "Simulated error" in data["error"]

@pytest.mark.usefixtures("init_database")
class TestAddPlaylist:

    """Tests for the POST /api/playlists endpoint.
    Takes only spotify or soundcloud playlist URLs. no longer takes IDs

    Test:
    - Adding a playlist with a valid URL - spotify
    - Adding a playlist with a valid URL - soundcloud
    - When playlist is already added
    - When an error
    - Adding a playlist with an invalid URL
    - Adding a playlist id
    """
    # Fake data for Spotify and SoundCloud playlists
    fake_spotify_playlist_data = {
        "name": "Fake Spotify Playlist",
        "external_id": "spotify123",
        "image_url": "http://fake.image/spotify.jpg",
        "track_count": 20,
        "url": "https://open.spotify.com/playlist/spotify123"
    }

    fake_soundcloud_playlist_data = {
        "name": "Fake Soundcloud Playlist",
        "external_id": "soundcloud123",
        "image_url": "http://fake.image/soundcloud.jpg",
        "track_count": 15,
        "url": "https://soundcloud.com/fake_playlist"
    }

    def test_add_playlist_valid_spotify(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.services.playlist_manager_service.SpotifyService.get_playlist_data",
            lambda url: self.fake_spotify_playlist_data
        )
        # Prevent actual track fetching.
        monkeypatch.setattr(
            "app.services.playlist_manager_service.TrackManagerService.fetch_playlist_tracks",
            lambda playlist_id: None
        )

        response = client.post('/api/playlists', json={"url_or_id": "https://open.spotify.com/playlist/sp123"})

        assert response.status_code == 201
        playlists = response.get_json()
        assert any(p["external_id"] == "spotify123" for p in playlists)

    def test_add_playlist_valid_soundcloud(self, client, monkeypatch):
        fake_soundcloud_tracks = [{"id": "track1"}, {"id": "track2"}]

        monkeypatch.setattr(
            "app.services.playlist_manager_service.SoundcloudService.get_playlist_data",
            lambda url: self.fake_soundcloud_playlist_data
        )
        monkeypatch.setattr(
            "app.services.playlist_manager_service.SoundcloudService.get_playlist_tracks",
            lambda url: fake_soundcloud_tracks
        )
        monkeypatch.setattr(
            "app.services.playlist_manager_service.TrackManagerService.fetch_playlist_tracks",
            lambda playlist_id: None
        )

        response = client.post('/api/playlists', json={"url_or_id": "https://soundcloud.com/username/playlist"})

        assert response.status_code == 201
        playlists = response.get_json()
        assert any(p["external_id"] == "soundcloud123" for p in playlists)

    def test_add_playlist_already_added(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.services.playlist_manager_service.SpotifyService.get_playlist_data",
            lambda url: self.fake_spotify_playlist_data
        )
        monkeypatch.setattr(
            "app.services.playlist_manager_service.TrackManagerService.fetch_playlist_tracks",
            lambda playlist_id: None
        )

        # First attempt: should add the playlist.
        response1 = client.post('/api/playlists', json={"url_or_id": "https://open.spotify.com/playlist/sp123"})
        assert response1.status_code == 201

        # Second attempt with the same URL should detect that the playlist already exists.
        response2 = client.post('/api/playlists', json={"url_or_id": "https://open.spotify.com/playlist/sp123"})
        assert response2.status_code == 400
        error_message = response2.get_json().get("error")
        assert error_message == "Playlist Already Exists"

    def test_add_playlist_not_error_spotify(self, client, monkeypatch):
        def fake_get_playlist_data_404(url):
            raise SpotifyException(http_status=404, msg="Not Found")

        monkeypatch.setattr(
            "app.services.playlist_manager_service.SpotifyService.get_playlist_data",
            fake_get_playlist_data_404
        )

        response = client.post('/api/playlists', json={"url_or_id": "https://open.spotify.com/playlist/error"})
        assert response.status_code == 400
        error_message = response.get_json().get("error")

        assert error_message == "Playlist not found. Please try another URL or ID."

    def test_add_playlist_invalid_url(self, client, monkeypatch):
        response = client.post('/api/playlists', json={"url_or_id": "invalid-url"})

        assert response.status_code == 400
        error_message = response.get_json().get("error")
        assert error_message == "URL Doesnt Look Right. Please try again with a valid URL."

    def test_add_playlist_id(self, client, monkeypatch):
        response = client.post('/api/playlists', json={"url_or_id": "12345"})
        assert response.status_code == 400
        error_message = response.get_json().get("error")
        assert error_message == "URL Doesnt Look Right. Please try again with a valid URL."