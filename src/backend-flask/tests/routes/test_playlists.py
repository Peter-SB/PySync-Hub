import pytest
from spotipy import SpotifyException

from app.models import Playlist
from app.repositories.playlist_repository import PlaylistRepository
from app.services.playlist_manager_service import PlaylistManagerService
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

    def test_add_playlist_preserves_track_order(self, client, monkeypatch):
        """Test that adding a playlist via endpoint preserves the correct track order."""
        # Add a Spotify playlist
        response = client.post('/api/playlists',
                               json={"url_or_id": "https://open.spotify.com/playlist/3bL14BgPXekKHep3RRdwGZ"})

        assert response.status_code == 201

        # Fetch the added playlist from the database
        added_playlist = Playlist.query.filter_by(external_id="3bL14BgPXekKHep3RRdwGZ").first()
        assert added_playlist is not None

        # Get playlist tracks through the relationship (which is ordered by track_order)
        playlist_tracks = added_playlist.tracks
        assert len(playlist_tracks) == 2

        # Verify the tracks are in the correct order
        # The mock data returns "Song One" first, then "Song Two"
        assert playlist_tracks[0].track.name == "Song One"
        assert playlist_tracks[0].track.artist == "Artist One"
        assert playlist_tracks[0].track_order == 0

        assert playlist_tracks[1].track.name == "Song Two"
        assert playlist_tracks[1].track.artist == "Artist Two"
        assert playlist_tracks[1].track_order == 1

        # Also verify via the API endpoint
        track_response = client.get(f'/api/playlist/{added_playlist.id}/tracks')
        assert track_response.status_code == 200
        tracks_data = track_response.get_json()
        
        assert len(tracks_data) == 2
        assert tracks_data[0]["name"] == "Song One"
        assert tracks_data[1]["name"] == "Song Two"

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
        response1 = client.post('/api/playlists', json={"url_or_id": "https://open.spotify.com/playlist/3bL14BgPXekKHep3RRdwGZ"})
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
        assert error_message == "Error Adding Playlist: URL Doesn't Look Right. Please try again with a valid URL."

    def test_add_playlist_id(self, client, monkeypatch):
        response = client.post('/api/playlists', json={"url_or_id": "12345"})
        assert response.status_code == 400
        error_message = response.get_json().get("error")
        assert error_message == "Error Adding Playlist: URL Doesn't Look Right. Please try again with a valid URL."

@pytest.mark.usefixtures("client", "init_database")
class TestUpdatePlaylist:
    """
    Tests for the PATCH /api/playlists/<playlist_id> endpoint.
    
    Tests Include:
    - Updating a playlist's date limit
    - Updating a playlist's track limit - Spotify
    - Updating a playlist's track limit - SoundCloud
    - Updating both date and track limits
    - Handling invalid date format
    - Handling non-existent playlist
    - Handling invalid track limit type
    """

    def test_update_playlist_date_limit(self, client, init_database):
        # Load test playlist data
        MockPlaylistDataHelper.load_data("Test Playlist 1")
        
        # Update playlist with date limit
        response = client.patch('/api/playlists/1', 
                              json={"date_limit": "2024-01-01"})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["date_limit"] == "2024-01-01T00:00:00"
        
        # Verify database update
        playlist = Playlist.query.get(1)
        assert playlist.date_limit.strftime("%Y-%m-%d") == "2024-01-01"
        assert len(playlist.tracks) == 1

    def test_update_playlist_track_limit_spotify(self, client, init_database):
        # Load test playlist data
        MockPlaylistDataHelper.load_data("Test Playlist 1")
        
        # Update playlist with track limit
        response = client.patch('/api/playlists/1', 
                              json={"track_limit": 1})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["track_limit"] == 1
        
        # Verify database update
        playlist = Playlist.query.get(1)
        assert playlist.track_limit == 1
        assert len(playlist.tracks) == 1

    def test_update_playlist_track_limit_soundcloud(self, client, init_database):
        # Load test playlist data
        MockPlaylistDataHelper.load_data("OMWHP")

        # Update playlist with track limit
        response = client.patch('/api/playlists/1',
                                json={"track_limit": 10})

        assert response.status_code == 200
        data = response.get_json()
        assert data["track_limit"] == 10

        # Verify database update
        playlist = Playlist.query.get(1)
        assert playlist.track_limit == 10
        assert len(playlist.tracks) == 10

    def test_update_playlist_both_limits(self, client, init_database):
        # Load test playlist data
        MockPlaylistDataHelper.load_data("Test Playlist 1")
        
        # Update playlist with both limits
        response = client.patch('/api/playlists/1', 
                              json={
                                  "date_limit": "2024-01-01",
                                  "track_limit": 10
                              })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["date_limit"] == "2024-01-01T00:00:00"
        assert data["track_limit"] == 10
        
        # Verify database update
        playlist = Playlist.query.get(1)
        assert playlist.date_limit.strftime("%Y-%m-%d") == "2024-01-01"
        assert playlist.track_limit == 10

    def test_update_playlist_invalid_date(self, client, init_database):
        # Load test playlist data
        MockPlaylistDataHelper.load_data("Test Playlist 1")
        
        # Try to update with invalid date format
        response = client.patch('/api/playlists/1', 
                              json={"date_limit": "invalid-date"})
        
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid date format" in data["error"]

    def test_update_playlist_nonexistent(self, client, init_database):
        # Try to update non-existent playlist
        response = client.patch('/api/playlists/999', 
                              json={"track_limit": 10})
        
        assert response.status_code == 404
        data = response.get_json()
        assert "Playlist not found" in data["error"]

    def test_update_playlist_invalid_track_limit(self, client, init_database):
        # Load test playlist data
        MockPlaylistDataHelper.load_data("Test Playlist 1")

        # Try to update with invalid track limit type
        response = client.patch('/api/playlists/1',
                              json={"track_limit": "not-a-number"})

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

@pytest.mark.usefixtures("client", "init_database")
class TestRefreshPlaylist:
    """
    Tests for the POST /api/playlists/<playlist_id>/refresh endpoint.
    
    Tests Include:
    - Refreshing a playlist successfully
    - Refreshing a non-existent playlist
    - Refreshing a disabled playlist
    - Handling errors during refresh
    """

    def test_refresh_playlist_success(self, client, init_database):
        MockPlaylistDataHelper.load_data("Test Playlist 1")
        
        initial_response = client.get('/api/playlists')
        initial_data = initial_response.get_json()
        initial_playlist = initial_data[0]
        
        response = client.post(f'/api/playlists/{initial_playlist["id"]}/refresh')
        assert response.status_code == 200
        
        updated_response = client.get('/api/playlists')
        updated_data = updated_response.get_json()
        updated_playlist = updated_data[0]
        
        assert updated_playlist["last_synced"] is not None
        assert updated_playlist["name"] == "Test Playlist 1"
        assert updated_playlist["platform"] == "spotify"
        assert len(updated_playlist["tracks"]) > 0

    def test_refresh_playlist_nonexistent(self, client, init_database):
        response = client.post('/api/playlists/999/refresh')
        assert response.status_code == 404
        data = response.get_json()
        assert "Playlist not found" in data["error"]

    def test_refresh_playlist_disabled(self, client, init_database):
        MockPlaylistDataHelper.load_data("Test Playlist 1")
        
        initial_response = client.get('/api/playlists')
        initial_data = initial_response.get_json()
        initial_playlist = initial_data[0]
        
        client.post('/api/playlists/toggle',
                   json={"playlist_id": initial_playlist["id"], "disabled": True})
        
        response = client.post(f'/api/playlists/{initial_playlist["id"]}/refresh')
        assert response.status_code == 200  # Should still work even if disabled
        
        updated_response = client.get('/api/playlists')
        updated_data = updated_response.get_json()
        updated_playlist = updated_data[0]
        assert updated_playlist["last_synced"] is not None

    def test_refresh_playlist_error(self, client, monkeypatch):
        MockPlaylistDataHelper.load_data("Test Playlist 1")
        
        initial_response = client.get('/api/playlists')
        initial_data = initial_response.get_json()
        playlist_id = initial_data[0]["id"]
        
        def mock_sync_playlists(*args, **kwargs):
            raise Exception("Simulated sync error")
        
        monkeypatch.setattr(PlaylistManagerService, "sync_playlists", mock_sync_playlists)
        
        response = client.post(f'/api/playlists/{playlist_id}/refresh')
        assert response.status_code == 500
        data = response.get_json()
        assert "Simulated sync error" in data["error"]
