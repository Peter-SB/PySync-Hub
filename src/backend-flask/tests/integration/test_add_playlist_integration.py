import os
import sqlite3
from pathlib import Path

import pytest

from app import create_app
from app.extensions import db
from app.models import Playlist, PlaylistTrack, Track
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
    Config.SOUNDCLOUD_CLIENT_ID = _settings.get("SOUNDCLOUD_CLIENT_ID", Config.SOUNDCLOUD_CLIENT_ID)
Config.SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", Config.SPOTIFY_CLIENT_ID)
Config.SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", Config.SPOTIFY_CLIENT_SECRET)
Config.SOUNDCLOUD_CLIENT_ID = os.environ.get("SOUNDCLOUD_CLIENT_ID", Config.SOUNDCLOUD_CLIENT_ID)

SPOTIFY_TEST_PLAYLIST_URL = os.environ.get(
    "SPOTIFY_TEST_PLAYLIST_URL",
    "https://open.spotify.com/playlist/3bL14BgPXekKHep3RRdwGZ?si=758a3108ca1e4909",
)
SOUNDCLOUD_TEST_PLAYLIST_URL = os.environ.get(
    "SOUNDCLOUD_TEST_PLAYLIST_URL",
    "https://soundcloud.com/joselito-break/sets/drummm",
)
YOUTUBE_TEST_PLAYLIST_URL = os.environ.get(
    "YOUTUBE_TEST_PLAYLIST_URL",
    "https://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj",
)


@pytest.fixture(autouse=True)
def mock_spotify_client():
    yield


@pytest.fixture(autouse=True)
def mock_soundcloud_client():
    yield


@pytest.fixture(autouse=True)
def mock_ytdlp():
    yield


@pytest.fixture(autouse=True)
def mock_youtube_service():
    yield


@pytest.fixture(scope="function")
def app(tmp_path):
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
    return app.test_client()


def _assert_db_rows(db_path, expected_platform):
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
def test_add_playlist_spotify_api(client, tmp_path, monkeypatch):
    if not (Config.SPOTIFY_CLIENT_ID and Config.SPOTIFY_CLIENT_SECRET):
        pytest.skip("Spotify API credentials not configured.")

    response = client.post(
        "/api/playlists",
        json={"url_or_id": SPOTIFY_TEST_PLAYLIST_URL, "track_limit": 5},
    )

    assert response.status_code == 201, "Error. {}".format(response.json) 
    db_path = tmp_path / "integration.db"
    _assert_db_rows(db_path, "spotify")


@pytest.mark.integration
def test_add_playlist_spotify_scraper(client, tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "SPOTIFY_CLIENT_ID", "", raising=False)
    monkeypatch.setattr(Config, "SPOTIFY_CLIENT_SECRET", "", raising=False)

    response = client.post(
        "/api/playlists",
        json={"url_or_id": SPOTIFY_TEST_PLAYLIST_URL, "track_limit": 5},
    )

    assert response.status_code == 201
    db_path = tmp_path / "integration.db"
    _assert_db_rows(db_path, "spotify")


@pytest.mark.integration
def test_add_playlist_soundcloud(client, tmp_path):
    if not Config.SOUNDCLOUD_CLIENT_ID:
        pytest.skip("SoundCloud client ID not configured.")

    response = client.post(
        "/api/playlists",
        json={"url_or_id": SOUNDCLOUD_TEST_PLAYLIST_URL, "track_limit": 5},
    )

    assert response.status_code == 201
    db_path = tmp_path / "integration.db"
    _assert_db_rows(db_path, "soundcloud")


@pytest.mark.integration
def test_add_playlist_youtube(client, tmp_path):
    response = client.post(
        "/api/playlists",
        json={"url_or_id": YOUTUBE_TEST_PLAYLIST_URL, "track_limit": 5},
    )

    assert response.status_code == 201
    db_path = tmp_path / "integration.db"
    _assert_db_rows(db_path, "youtube")
