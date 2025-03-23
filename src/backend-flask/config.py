import logging
import os
import sys
import yaml

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

    # Database
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_PATH, 'database.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    FLASK_APP = "app.py"
    FLASK_ENV = "development"
    DEBUG = True  # Enables auto-reload

    SPOTIFY_CLIENT_ID = None
    SPOTIFY_CLIENT_SECRET = None
    SOUNDCLOUD_CLIENT_ID = None

    with open(SETTINGS_PATH, 'r') as f:
        settings = yaml.safe_load(f)
    SPOTIFY_CLIENT_ID = settings.get('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = settings.get('SPOTIFY_CLIENT_SECRET')
    SOUNDCLOUD_CLIENT_ID = settings.get('SOUNDCLOUD_CLIENT_ID')

    @classmethod
    def load_settings(cls):
        with open(cls.SETTINGS_PATH, 'r') as f:
            settings = yaml.safe_load(f)
        cls.SPOTIFY_CLIENT_ID = settings.get('SPOTIFY_CLIENT_ID')
        cls.SPOTIFY_CLIENT_SECRET = settings.get('SPOTIFY_CLIENT_SECRET')
        cls.SOUNDCLOUD_CLIENT_ID = settings.get('SOUNDCLOUD_CLIENT_ID')


#Config.load_settings()


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    SPOTIFY_CLIENT_ID = 'dummy_client_id'
    SPOTIFY_CLIENT_SECRET = 'dummy_client_secret'
