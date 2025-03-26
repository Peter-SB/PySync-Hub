import os
import sys

import pytest
from app import create_app, SpotifyService
from app.services.platform_services.soundcloud_service import SoundcloudService
from config import TestConfig
from app.extensions import db
from tests.mocks.mock_spotify_client import MockSpotifyClient
from tests.mocks.mock_soundcloud_service import MockSoundcloudService
from tests.mocks.mock_ytdl import MockYoutubeDL


@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for tests as well as setup and teardown the db"""
    app = create_app(TestConfig)  # Create the app normally with create_app

    ctx = app.app_context()
    ctx.push()

    db.create_all()

    yield app  # Provide the app instance to tests

    db.drop_all()
    ctx.pop()

@pytest.fixture(scope='function', autouse=True)
def init_database(app):
    """
    Ensure a clean database before each test by dropping all tables and creating new ones.
    This is slower than using transactions, but necessary as code commits regularly.
    """
    # Remove any existing data and re-create all tables.
    db.session.remove()
    db.drop_all()
    db.create_all()
    yield db
    # Cleanup after the test.
    db.session.remove()
    db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Returns a test client for making requests."""
    return app.test_client()

@pytest.fixture(autouse=True)
def mock_spotify_client(monkeypatch):
    """Automatically replace SpotifyService.get_client for all tests"""
    print("Mocking SpotifyService.get_client")
    monkeypatch.setattr(SpotifyService, "get_client", lambda: MockSpotifyClient())

@pytest.fixture(autouse=True)
def mock_soundcloud_client(monkeypatch):
    """Automatically replace DummySoundcloudService for all tests"""
    print("Mocking SoundcloudService._make_http_get_request")
    monkeypatch.setattr("app.services.platform_services.soundcloud_service.SoundcloudService", MockSoundcloudService)

@pytest.fixture(autouse=True)
def mock_ytdlp(monkeypatch):
    # Patch the YoutubeDL used in SpotifyDownloadService so that all calls use DummyYoutubeDL.
    monkeypatch.setattr("app.services.download_services.spotify_download_service.YoutubeDL", MockYoutubeDL)
