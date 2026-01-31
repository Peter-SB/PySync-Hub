"""Integration tests for Spotify scraper service with response capturing."""
import os
import sqlite3
from pathlib import Path

import pytest

from app import create_app
from app.extensions import db
from app.models import Playlist, PlaylistTrack, Track
from app.services.platform_services.spotify_scraper_service import SpotifyScraperService
from config import Config
from dotenv import find_dotenv, load_dotenv
import yaml

_here = Path(__file__).resolve()
_backend_dir = _here.parents[2]
_repo_dir = _here.parents[4]

load_dotenv(find_dotenv(usecwd=True))
load_dotenv(_backend_dir / ".env", override=False)
load_dotenv(_repo_dir / ".env", override=False)

_settings_path = _repo_dir / "settings.yml"
if _settings_path.exists():
    with _settings_path.open("r", encoding="utf-8") as handle:
        _settings = yaml.safe_load(handle) or {}
    Config.SPOTIFY_CLIENT_ID = _settings.get("SPOTIFY_CLIENT_ID", Config.SPOTIFY_CLIENT_ID)
    Config.SPOTIFY_CLIENT_SECRET = _settings.get("SPOTIFY_CLIENT_SECRET", Config.SPOTIFY_CLIENT_SECRET)

Config.SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", Config.SPOTIFY_CLIENT_ID)
Config.SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", Config.SPOTIFY_CLIENT_SECRET)

# Test playlist URL - use a small public playlist
SPOTIFY_TEST_PLAYLIST_URL = os.environ.get(
    "SPOTIFY_TEST_PLAYLIST_URL",
    "https://open.spotify.com/playlist/5WWIc4WKOgFjn8Df5wjBTG",
)


@pytest.fixture(scope="function")
def app(tmp_path):
    """Create Flask app with test database."""
    db_path = tmp_path / "integration.db"
    db_uri = f"sqlite:///{db_path.resolve().as_posix()}"

    class IntegrationConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = db_uri
        WTF_CSRF_ENABLED = False

    app = create_app(IntegrationConfig)
    ctx = app.app_context()
    ctx.push()
    db.drop_all()
    db.create_all()

    yield app

    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture(scope="function")
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def captured_requests_dir(tmp_path):
    """Create temporary directory for captured responses."""
    capture_dir = tmp_path / "captured_requests"
    capture_dir.mkdir()
    return str(capture_dir)


def _assert_db_rows(db_path, expected_platform):
    """Assert database contains expected playlist and track data."""
    playlist_count = db.session.query(Playlist).count()
    track_count = db.session.query(Track).count()
    playlist_track_count = db.session.query(PlaylistTrack).count()

    assert playlist_count == 1
    assert track_count >= 1
    assert playlist_track_count >= 1

    playlist = db.session.query(Playlist).first()
    assert playlist.platform == expected_platform
    assert playlist.external_id

    assert db_path.exists()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM playlists")
        row_count = cursor.fetchone()[0]
        assert row_count == 1


@pytest.mark.integration
def test_add_playlist_spotify_scraper_with_response_capture(client, tmp_path, monkeypatch, captured_requests_dir):
    """Test adding a Spotify playlist using scraper and capture responses for unit tests."""
    # Force use of scraper by clearing API credentials and forcing factory to use scraper
    monkeypatch.setattr(Config, "SPOTIFY_CLIENT_ID", "", raising=False)
    monkeypatch.setattr(Config, "SPOTIFY_CLIENT_SECRET", "", raising=False)
    
    # Force the factory to use scraper service instead of API service
    from app.services.platform_services.platform_services_factory import PlatformServiceFactory
    monkeypatch.setattr(
        PlatformServiceFactory, 
        "_get_spotify_service", 
        staticmethod(lambda: SpotifyScraperService)
    )

    # Make the API call to add playlist
    response = client.post(
        "/api/playlists",
        json={"url_or_id": SPOTIFY_TEST_PLAYLIST_URL, "track_limit": 5},
    )

    # Assert successful addition
    assert response.status_code == 201
    db_path = tmp_path / "integration.db"
    _assert_db_rows(db_path, "spotify")

    # Verify playlist was added correctly
    playlist = db.session.query(Playlist).first()
    assert playlist.name
    assert playlist.image_url
    assert playlist.track_count >= 1

    # Verify tracks were added
    tracks = db.session.query(Track).all()
    assert len(tracks) >= 1
    for track in tracks:
        assert track.name
        assert track.artist
        assert track.platform == "spotify"
        assert track.platform_id

    print(f"\n✓ Playlist '{playlist.name}' successfully added with {len(tracks)} tracks")
    print(f"✓ Playlist ID: {playlist.external_id}")
    print(f"✓ Image URL: {playlist.image_url}")
    print(f"✓ First track: {tracks[0].name} by {tracks[0].artist}")


@pytest.mark.integration
def test_spotify_scraper_get_playlist_data_with_save(app, captured_requests_dir, monkeypatch):
    """Test SpotifyScraperService.get_playlist_data with response saving."""
    # Force use of scraper
    monkeypatch.setattr(Config, "SPOTIFY_CLIENT_ID", "", raising=False)
    monkeypatch.setattr(Config, "SPOTIFY_CLIENT_SECRET", "", raising=False)
    
    # Get playlist data with response saving
    playlist_data = SpotifyScraperService.get_playlist_data(
        SPOTIFY_TEST_PLAYLIST_URL,
    )

    # Assert playlist data is valid
    assert playlist_data["name"]
    assert playlist_data["external_id"]
    assert playlist_data["platform"] == "spotify"
    assert playlist_data["url"] == SPOTIFY_TEST_PLAYLIST_URL
    assert playlist_data["track_count"] >= 1
