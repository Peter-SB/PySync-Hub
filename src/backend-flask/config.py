import logging
import os
import sys
import yaml
from sqlalchemy import NullPool


def get_base_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.join(sys._MEIPASS, "../")  # When running as an executable
    else:
        base_path = os.path.abspath(".")
    return base_path


class Config:
    BASE_PATH = os.path.join(get_base_path(), "../../")
    SETTINGS_PATH = os.path.join(BASE_PATH, "settings.yml")
    DOWNLOAD_FOLDER = os.path.join(BASE_PATH, 'music_downloads')
    EXPORT_FOLDER = os.path.join(BASE_PATH, 'rekordbox_library_exports')
    EXPORT_FILENAME = 'rekordbox.xml'
    FFMPEG_FOLDER = os.path.join(get_base_path(), '../ffmpeg')

    # Database
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_PATH, 'database.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "timeout": 30,            # seconds to wait for a lock
            "check_same_thread": False
        },
        "poolclass": NullPool,       # avoid holding connections in some app designs
        "pool_pre_ping": True
    }

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    FLASK_APP = "app.py"
    FLASK_ENV = "development"
    DEBUG = False  # Enables auto-reload
    TESTING = False

    SPOTIFY_CLIENT_ID = None
    SPOTIFY_CLIENT_SECRET = None
    SPOTIFY_OAUTH_SCOPE = 'user-library-read playlist-read-private user-read-recently-played'
    SPOTIFY_REDIRECT_URI = 'http://localhost:5000/api/spotify_auth/callback'
    SPOTIFY_TOKEN_CACHE = '.spotipyoauthcache'
    SPOTIFY_PORT_NUMBER = 8888
    ENABLE_SPOTIFY_RECENTLY_PLAYED = False

    SOUNDCLOUD_CLIENT_ID = None

    if not os.path.exists(SETTINGS_PATH) and not TESTING:
        default_settings = {
            "SPOTIFY_CLIENT_ID": "",
            "SPOTIFY_CLIENT_SECRET": "",
            "SOUNDCLOUD_CLIENT_ID": "",
            "ENABLE_SPOTIFY_RECENTLY_PLAYED": False
        }
        with open(SETTINGS_PATH, 'w') as f:
            yaml.safe_dump(default_settings, f, default_flow_style=False)
        print(f"Created new settings file at: {SETTINGS_PATH}")

    with open(SETTINGS_PATH, 'r') as f: # todo: handle creating new file better
        settings = yaml.safe_load(f)
    SPOTIFY_CLIENT_ID = settings.get('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = settings.get('SPOTIFY_CLIENT_SECRET')
    SOUNDCLOUD_CLIENT_ID = settings.get('SOUNDCLOUD_CLIENT_ID')
    ENABLE_SPOTIFY_RECENTLY_PLAYED = settings.get('ENABLE_SPOTIFY_RECENTLY_PLAYED', False)

    @classmethod
    def load_settings(cls):
        with open(cls.SETTINGS_PATH, 'r') as f:
            settings = yaml.safe_load(f)
        cls.SPOTIFY_CLIENT_ID = settings.get('SPOTIFY_CLIENT_ID')
        cls.SPOTIFY_CLIENT_SECRET = settings.get('SPOTIFY_CLIENT_SECRET')
        cls.SOUNDCLOUD_CLIENT_ID = settings.get('SOUNDCLOUD_CLIENT_ID')
        cls.ENABLE_SPOTIFY_RECENTLY_PLAYED = settings.get('ENABLE_SPOTIFY_RECENTLY_PLAYED', False)


#Config.load_settings()


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

    SPOTIFY_CLIENT_ID = 'dummy_client_id'
    SPOTIFY_CLIENT_SECRET = 'dummy_client_secret'
    SOUNDCLOUD_CLIENT_ID = "dummy_soundcloud_client_id"
