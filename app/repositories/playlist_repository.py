import logging
from datetime import datetime
from typing import List
from app.extensions import db
from app.models import Playlist

logger = logging.getLogger(__name__)

class PlaylistRepository:
    @staticmethod
    def get_all_playlists() -> List[Playlist]:
        logger.info("Fetching all playlists")
        return Playlist.query.order_by(Playlist.created_at.desc()).all()

    @staticmethod
    def get_all_active_playlists() -> List[Playlist]:
        logger.info("Fetching all playlists")
        return Playlist.query.order_by(Playlist.created_at.desc()).filter_by(disabled=False).all()

    @staticmethod
    def get_playlists_by_ids(playlist_ids: List[int]) -> List[Playlist]:
        logger.info(f"Fetching playlists with IDs: {playlist_ids}")
        return Playlist.query.filter(Playlist.id.in_(playlist_ids)).order_by(Playlist.created_at.desc()).all()

    @staticmethod
    def get_playlist_by_id(playlist_id: int) -> Playlist:
        logger.info(f"Fetching playlists with IDs: {playlist_id}")
        return Playlist.query.filter(Playlist.id == playlist_id).first()

    @staticmethod
    def get_playlist(playlist_id):
        logger.info(f"Fetching playlist with ID: {playlist_id}")
        return db.session.get(Playlist, playlist_id)

    @staticmethod
    def create_playlist(playlist_data):
        logger.info(f"Creating new playlist: {playlist_data['name']}, data {playlist_data}")
        playlist = Playlist(
            name=playlist_data['name'],
            platform=playlist_data['platform'],
            external_id=playlist_data['external_id'],
            last_synced=datetime.utcnow(),
            created_at=datetime.utcnow(),
            image_url=playlist_data.get('image_url'),
            track_count=playlist_data.get('track_count'),
            url=playlist_data('url'),
            disabled=False
        )
        db.session.add(playlist)
        db.session.commit()
        logger.info("Created new playlist with external_id: %s", playlist.external_id)
        return playlist

    @staticmethod
    def update_playlist(playlist, update_data):
        logger.info(f"Updating playlist: {playlist.external_id}, data: {update_data}")
        playlist.name = update_data.get('name', playlist.name)
        playlist.image_url = update_data.get('image_url', playlist.image_url)
        playlist.track_count = update_data.get('track_count', playlist.track_count)
        playlist.last_synced = datetime.utcnow()
        playlist.disabled = update_data.get('disabled', playlist.disabled)
        db.session.commit()
        logger.info("Updated playlist ID: %s", playlist.id)
        return playlist

    @staticmethod
    def delete_playlists_by_ids(playlist_ids):
        Playlist.query.filter(Playlist.id.in_(playlist_ids)).delete(synchronize_session=False)
        db.session.commit()
        logger.info("Deleted playlists with IDs: %s", playlist_ids)


