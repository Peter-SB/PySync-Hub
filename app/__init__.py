import logging
import os
import sys

from flask import Flask
from app.extensions import db, socketio, migrate
from app.repositories.playlist_repository import PlaylistRepository
from app.services.spotify_service import SpotifyService
from app.workers.download_worker import DownloadManager
from config import Config

def create_app(app_config=Config):
    app = Flask(__name__)
    app.config.from_object(app_config)


    db.init_app(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate
    socketio.init_app(app)


    # Configure Logging
    logging.basicConfig(
        level=logging.INFO,  # Change to DEBUG for more verbosity
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)  # Ensures logs are visible in Docker
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("Flask application initialized")

    # Initialize database
    with app.app_context():
        from app.models import Playlist
        db.create_all()

    from app.routes import main
    app.register_blueprint(main)

    if not app.config.get("TESTING"):
        os.makedirs(app.config.get("DOWNLOAD_FOLDER"), exist_ok=True)

    app.download_manager = DownloadManager(app)

    with app.app_context():
        PlaylistRepository.reset_download_statuses_to_ready()

    return app

# python -m flask run --debug
