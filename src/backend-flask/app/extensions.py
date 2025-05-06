from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO


db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO(async_mode='threading', cors_allowed_origins="*")

def emit_error_message(playlist_id, error_message):
    """ Helper function to emit error messages via WebSocket. """
    socketio.emit("download_error", {
        "id": playlist_id,
        "error": error_message
    })