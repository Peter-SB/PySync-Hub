import logging
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.services.spotify_service import SpotifyService
from config import Config

#import flask_migrate
#import flask_wtf

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Load config from file

    db.init_app(app)

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

    #
    from app.routes import main
    app.register_blueprint(main)

    SpotifyService.get_client()

    return app

# python -m flask run --debug