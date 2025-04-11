import logging
import os
import sys

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_migrate import upgrade, init, stamp

from app.extensions import db, socketio, migrate
from app.repositories.playlist_repository import PlaylistRepository
from app.services.platform_services.spotify_service import SpotifyService
from app.workers.download_worker import DownloadManager
from config import Config

def create_app(app_config=Config):
    app = Flask(__name__, static_folder='../build', static_url_path='')
    app.config.from_object(app_config)
    CORS(app, 
        resources={r"/*": {"origins": "*", 
                            "allow_headers": ["Content-Type", "Authorization"],
                            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]}})

    # Serve React App
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

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
    logger.info(f"Base Path={Config.BASE_PATH}")
    logger.info(f"DB Path={os.path.normpath(Config.SQLALCHEMY_DATABASE_URI)}")
    logger.info(f"Settings Path={os.path.normpath(Config.SETTINGS_PATH)}")
    logger.info("Flask application initialized")

    # Initialize database
    with app.app_context():
        from app.models import Playlist
        db.create_all()
        # upgrade()
    # with app.app_context():
    #     _handle_database_migrations(app, logger)

    from app.routes import api
    app.register_blueprint(api)

    if not app.config.get("TESTING"):
        os.makedirs(os.path.join(os.getcwd(), app.config.get("DOWNLOAD_FOLDER")), exist_ok=True)

    app.download_manager = DownloadManager(app)

    with app.app_context():
        PlaylistRepository.reset_download_statuses_to_ready()

    return app

def _handle_database_migrations(app, logger):
    try:
        # Automatically run pending migrations
        upgrade()
    except Exception as e:
        # Log the error, and as a fallback, create tables (useful for a fresh install)
        logger.error("Auto migration failed: %s", e)
        db.create_all()

    # migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    #
    # if not os.path.exists(migrations_dir):
    #     # Initialize migrations directory if missing
    #     init()
    #     stamp()  # Pretend the current DB state is the initial state
    #     migrate(message="Initial migration")
    #     upgrade()
    # else:
    #     try:
    #         # Attempt to migrate and upgrade
    #         migrate(message="Auto migration")
    #     except Exception as e:
    #         print(f"Migration error: {e}")
    #     upgrade()

# python -m flask run --debug
