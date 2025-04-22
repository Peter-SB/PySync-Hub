import logging
from datetime import datetime
from typing import List

from app.extensions import db, socketio
from app.models import Playlist, PlaylistTrack, Track, Folder

logger = logging.getLogger(__name__)


class FolderRepository:
    def get_folder_by_id(folder_id):
        """Retrieve a folder by its ID."""
        return db.session.query(Folder).get(folder_id)
