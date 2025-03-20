import threading
import pytest
from flask import Flask
from app.models import Playlist
from app.services.download_services.spotify_download_service import SpotifyDownloadService
from app.workers.download_worker import DownloadManager


# Fixture for a dummy Flask application
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    with app.app_context():
        yield app

# Fixture for an instance of DownloadManager.
@pytest.fixture
def download_manager(app):
    manager = DownloadManager()
    yield manager
    # Optionally: if you add a shutdown mechanism to DownloadManager,
    # call it here to gracefully stop the background thread.

# Test when a valid playlist is found.
def test_valid_playlist(app, download_manager, monkeypatch):
    calls = []  # To record calls to the download function

    # Create a dummy playlist object.
    dummy_playlist = type("DummyPlaylist", (), {"id": 1})()

    # Monkeypatch Playlist.query.get to return the dummy playlist when playlist_id == 1.
    def dummy_get(playlist_id):
        return dummy_playlist if playlist_id == 1 else None

    # Replace the Playlist.query with one that uses our dummy_get.
    DummyQuery = type("DummyQuery", (), {"get": staticmethod(dummy_get)})
    monkeypatch.setattr(Playlist, "query", DummyQuery)

    # Monkeypatch SpotifyDownloadService.download_playlist to record its call.
    def dummy_download_playlist(playlist, cancellation_flags):
        calls.append((playlist, cancellation_flags))
    monkeypatch.setattr(SpotifyDownloadService, "download_playlist", dummy_download_playlist)

    # Add the valid playlist id to the queue.
    download_manager.add_to_queue(1)

    # Wait for the queue to be processed.
    download_manager.download_queue.join()

    # Verify that the download function was called exactly once with the dummy playlist.
    assert len(calls) == 1
    assert calls[0][0] == dummy_playlist

# Test when an invalid playlist id is added.
def test_invalid_playlist(app, download_manager, monkeypatch):
    calls = []  # To record calls to the download function

    # Make Playlist.query.get always return None.
    def dummy_get(playlist_id):
        return None
    DummyQuery = type("DummyQuery", (), {"get": staticmethod(dummy_get)})
    monkeypatch.setattr(Playlist, "query", DummyQuery)

    # Monkeypatch the download function as before.
    def dummy_download_playlist(playlist, cancellation_flags):
        calls.append((playlist, cancellation_flags))
    monkeypatch.setattr(SpotifyDownloadService, "download_playlist", dummy_download_playlist)

    # Add an invalid playlist id.
    download_manager.add_to_queue(999)
    download_manager.download_queue.join()

    # Because the playlist wasn’t found, the download function should never be called.
    assert len(calls) == 0

# Test the cancel_download functionality.
def test_cancel_download(app, download_manager):
    # Manually add a cancellation flag (a threading.Event) for playlist id 1.
    event = threading.Event()
    download_manager.cancellation_flags[1] = event

    download_manager.cancel_download(1)

    # The event should be set after cancellation.
    assert event.is_set()
