import os


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Database
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/pysync.db'  # os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pysync.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    FLASK_APP = "app.py"
    FLASK_ENV = "development"
    DEBUG = True  # Enables auto-reload

    # Spotify
    SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

    # Downloads Folder
    DOWNLOAD_FOLDER = 'downloads'
    EXPORT_FOLDER = './rekordbox_library_exports'

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    SPOTIFY_CLIENT_ID = 'dummy_client_id'
    SPOTIFY_CLIENT_SECRET = 'dummy_client_secret'
