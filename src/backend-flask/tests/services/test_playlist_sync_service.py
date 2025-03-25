# tests/test_playlist_sync_service.py
import pytest
from app.models import Playlist
from app.services.playlist_manager_service import PlaylistManagerService
from app import extensions

def fake_get_playlist_data(external_id: str) -> dict:
    return {
        'name': f'Fake Playlist {external_id}',
        'external_id': external_id,
        'image_url': 'http://example.com/image.jpg',
        'track_count': 10,
    }

def test_get_spotify_playlist(client, mock_spotify_service):
    """Test that /spotify/playlist/<playlist_id> uses the mock service."""
    response = client.get("/playlist/test123")
    assert response.status_code == 200

    data = response.json
    assert data["name"] == "Fake Test Playlist"
    assert data["external_id"] == "test123"
    assert data["image_url"] == "http://test.com/image.jpg"
    assert data["track_count"] == 5

    # Verify that the mock was actually called
    mock_spotify_service.get_playlist_data.assert_called_once_with("test123")

def test_sync_playlists_unit(monkeypatch, db_session):
    """
    Test that syncing a playlist updates its details.
    """
    # Create a dummy playlist
    playlist = Playlist(
        name='Old Name',
        platform='spotify',
        external_id='fake123',
        image_url='http://oldimage.com',
        track_count=5
    )
    db.session.add(playlist)
    db.session.commit()

    # Patch SpotifyService.get_playlist_data to use our fake function.
    # monkeypatch.setattr(
    #     "app.services.sync.SpotifyService.get_playlist_data",
    #     fake_get_playlist_data
    # )
    monkeypatch.setattr(
        "app.services.spotify_playlist_service.SpotifyService.get_playlist_data",
        fake_get_playlist_data
    )


    # Run sync on this playlist
    PlaylistManagerService.sync_playlists([playlist.id])

    # Refresh the playlist from the database
    synced_playlist = Playlist.query.get(playlist.id)
    assert synced_playlist.name == 'Fake Playlist fake123'
    assert synced_playlist.image_url == 'http://example.com/image.jpg'
    assert synced_playlist.track_count == 10
    assert synced_playlist.last_synced is not None
