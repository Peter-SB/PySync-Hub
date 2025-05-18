from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO


db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO(async_mode='threading', cors_allowed_origins="*")

def emit_error_message(playlist_id, error_message):
    """ Helper function to emit error messages via WebSocket. """

    # Handle specific error messages
    if "Sign in to confirm your age" in error_message:
        return

    if "No such file or directory" in error_message:
        return

    socketio.emit("download_error", {
        "id": playlist_id,
        "error": error_message
    })

def emit_playlist_sync_update(playlist_id, track_count, tracks=None):
    """ Helper function to emit playlist sync updates via WebSocket. """
    update_data = {
        "id": playlist_id,
        "track_count": track_count
    }
    
    # Include tracks data if provided
    if tracks is not None:
        update_data["tracks"] = tracks
        
    socketio.emit("playlist_sync_update", update_data)