import logging
import os
import sys

import yaml

logger = logging.getLogger(__name__)

def get_settings_path():
    if getattr(sys, 'frozen', False):  # Running as PyInstaller executable
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    print(f"Base path: {base_path}")
    return os.path.join(base_path, "../settings.yml")

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SETTINGS_PATH = get_settings_path()

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS  # When running as an executable
    else:
        base_path = os.path.abspath(".")


    # Database
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(base_path, 'database.db')}"
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/pysync.db'  # os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pysync.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    FLASK_APP = "app.py"
    FLASK_ENV = "development"
    DEBUG = True  # Enables auto-reload

    # with open(SETTINGS_PATH, 'r') as f:
    #     settings = yaml.safe_load(f)

    SPOTIFY_CLIENT_ID = None
    SPOTIFY_CLIENT_SECRET = None
    SOUNDCLOUD_CLIENT_ID = None

    # Downloads Folder
    DOWNLOAD_FOLDER = '../downloads'
    EXPORT_FOLDER = '../rekordbox_library_exports'

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
