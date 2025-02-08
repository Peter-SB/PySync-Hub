# tests/test_playlist_sync_service.py
import pytest
from app.models import Playlist
from app.services.playlist_service import PlaylistService
from app import db

def fake_get_playlist_data(external_id: str) -> dict:
    return {
        'name': f'Fake Playlist {external_id}',
        'external_id': external_id,
        'image_url': 'http://example.com/image.jpg',
        'track_count': 10,
    }

def test_sync_playlists_unit(monkeypatch, db):
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
    monkeypatch.setattr(
        "app.services.sync.SpotifyService.get_playlist_data",
        fake_get_playlist_data
    )

    # Run sync on this playlist
    PlaylistService.fetch_playlists([playlist.id])

    # Refresh the playlist from the database
    synced_playlist = Playlist.query.get(playlist.id)
    assert synced_playlist.name == 'Fake Playlist fake123'
    assert synced_playlist.image_url == 'http://example.com/image.jpg'
    assert synced_playlist.track_count == 10
    assert synced_playlist.last_synced is not None
