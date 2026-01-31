import logging
import os
import sys

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_migrate import upgrade, init, stamp

from app.extensions import db, socketio, migrate
from app.repositories.playlist_repository import PlaylistRepository
from app.workers.download_worker import DownloadManager
from app.database_migrator import DatabaseMigrator
from config import Config

def set_sqlite_pragmas(db):
    # Set PRAGMA settings to reduce locking issues
    from sqlalchemy import text
    with db.engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.execute(text("PRAGMA synchronous=NORMAL;"))
        conn.execute(text("PRAGMA busy_timeout=3000;"))

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

    # Set SQLite PRAGMAs after db is initialized
    with app.app_context():
        set_sqlite_pragmas(db)

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

    # todo: refactor to a setup_database function
    # Run database migrations
    db_path = app_config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    if os.path.exists(db_path) and not app.config.get("TESTING"):
        logger.info(f"Running database migrations on {db_path}")
        DatabaseMigrator.run_migrations(db_path)
    
    # Initialize database
    with app.app_context():
        from app.models import Playlist, Folder
        db.create_all()

    # Register folder routes
    # todo: refactor to function, make new blueprints for other routes
    from app.routes import api
    from app.routes.folders import bp as folders_bp
    app.register_blueprint(api)
    app.register_blueprint(folders_bp)

    if not app.config.get("TESTING"):
        os.makedirs(os.path.join(os.getcwd(), app.config.get("DOWNLOAD_FOLDER")), exist_ok=True)

    app.download_manager = DownloadManager(app)

    with app.app_context():
        PlaylistRepository.reset_download_statuses_to_ready()

    return app


# python -m flask run --debug
