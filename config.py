import os

import yaml


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SETTINGS_PATH = os.path.join(BASE_DIR, 'settings.yml')

    # Database
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/pysync.db'  # os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pysync.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    FLASK_APP = "app.py"
    FLASK_ENV = "development"
    DEBUG = True  # Enables auto-reload

    with open(SETTINGS_PATH, 'r') as f:
        settings = yaml.safe_load(f)

    SPOTIFY_CLIENT_ID = None
    SPOTIFY_CLIENT_SECRET = None
    SOUNDCLOUD_CLIENT_ID = None

    # Downloads Folder
    DOWNLOAD_FOLDER = 'downloads'
    EXPORT_FOLDER = './rekordbox_library_exports'

    @classmethod
    def load_settings(cls):
        with open(cls.SETTINGS_PATH, 'r') as f:
            settings = yaml.safe_load(f)
        cls.SPOTIFY_CLIENT_ID = settings.get('SPOTIFY_CLIENT_ID')
        cls.SPOTIFY_CLIENT_SECRET = settings.get('SPOTIFY_CLIENT_SECRET')
        cls.SOUNDCLOUD_CLIENT_ID = settings.get('SOUNDCLOUD_CLIENT_ID')


Config.load_settings()


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    SPOTIFY_CLIENT_ID = 'dummy_client_id'
    SPOTIFY_CLIENT_SECRET = 'dummy_client_secret'
