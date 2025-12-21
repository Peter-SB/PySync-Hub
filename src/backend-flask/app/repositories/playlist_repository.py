import logging
from datetime import datetime
from typing import List

from app.extensions import db, socketio
from app.models import Playlist, PlaylistTrack, Track
from app.utils.sqlite_utils import commit_with_retries

logger = logging.getLogger(__name__)


class PlaylistRepository:
    @staticmethod
    def get_all_playlists() -> List[Playlist]:
        logger.debug("Fetching all playlists")
        return Playlist.query.order_by(Playlist.created_at.desc()).all()

    @staticmethod
    def get_all_active_playlists() -> List[Playlist]:
        logger.debug("Fetching all playlists")
        return Playlist.query.order_by(Playlist.created_at.desc()).filter_by(disabled=False).all()

    @staticmethod
    def get_playlists_by_ids(playlist_ids: List[int]) -> List[Playlist]:
        logger.debug(f"Fetching playlists with IDs: {playlist_ids}")
        return Playlist.query.filter(Playlist.id.in_(playlist_ids)).order_by(Playlist.created_at.desc()).all()

    @staticmethod
    def get_playlist_by_id(playlist_id: int) -> Playlist:
        logger.debug(f"Fetching playlists with IDs: {playlist_id}")
        return Playlist.query.filter(Playlist.id == playlist_id).first()

    @staticmethod
    def get_playlist_by_url(url: str) -> Playlist:
        logger.debug(f"Fetching playlists with URL: {url}")
        return Playlist.query.filter(Playlist.url == url).first()

    @staticmethod
    def get_playlist(playlist_id):
        logger.info(f"Fetching playlist with ID: {playlist_id}")
        return db.session.get(Playlist, playlist_id)

    @staticmethod
    def get_playlist_tracks(playlist_id) -> List[Track]:
        logger.debug("Fetching playlist tracks")
        playlist = PlaylistRepository.get_playlist_by_id(playlist_id)
        return [pt.track.to_dict() for pt in playlist.tracks if pt.track]

    @staticmethod
    def create_playlist(playlist_data):
        logger.info(f"Creating new playlist: {playlist_data['name']}, data {playlist_data}")
        playlist = Playlist(
            name=playlist_data['name'],
            platform=playlist_data['platform'],
            external_id=playlist_data['external_id'],
            last_synced=None,
            created_at=datetime.utcnow(),
            image_url=playlist_data.get('image_url'),
            track_count=playlist_data.get('track_count'),
            url=playlist_data.get('url'),
            disabled=False,
            download_status="ready",
            custom_order=-1
        )
        db.session.add(playlist)

        try:
            commit_with_retries(db.session)
            logger.info("Added new %s playlist with external_id: %s", playlist_data['platform'],
                        playlist_data['external_id'])
        except Exception as e:
            logger.error("Database commit failed when adding playlist: %s", e, exc_info=True)
            db.session.rollback()
            return "Database Error"

        return playlist

    @staticmethod
    def update_playlist(playlist, update_data):
        logger.info(f"Updating playlist: {playlist.external_id}, data: {update_data}")
        playlist.name = update_data.get('name', playlist.name)
        playlist.image_url = update_data.get('image_url', playlist.image_url)
        playlist.track_count = update_data.get('track_count', playlist.track_count)
        playlist.last_synced = datetime.utcnow()
        playlist.disabled = update_data.get('disabled', playlist.disabled)
        commit_with_retries(db.session)
        logger.info("Updated playlist ID: %s", playlist.id)
        return playlist

    @staticmethod
    def delete_playlists_by_ids(playlist_ids):
        PlaylistTrack.query.filter(PlaylistTrack.playlist_id.in_(playlist_ids)).delete(synchronize_session=False)
        Playlist.query.filter(Playlist.id.in_(playlist_ids)).delete(synchronize_session=False)

        commit_with_retries(db.session)
        logger.info("Deleted playlists with IDs: %s", playlist_ids)

    @staticmethod
    def set_download_progress(playlist, progress):
        socketio.emit("download_status", {
            "id": playlist.id,
            "status": "downloading",
            "progress": progress
        })

    @staticmethod
    def set_download_status(playlist, status):
        if status == "ready":
            playlist.download_status = 'ready'
            download_progress = playlist.downloaded_track_count/len(playlist.tracks) * 100 if len(playlist.tracks) > 0 else 0
            socketio.emit("download_status", {"id": playlist.id, "status": "ready", "progress": download_progress})
        elif status == "queued":
            playlist.download_status = 'queued'
        elif status == "downloading":
            playlist.download_status = 'downloading'
            socketio.emit("download_status", {"id": playlist.id, "status": "downloading", "progress": 0})
        else:
            logger.error("No status %s", status)

        commit_with_retries(db.session)

    @staticmethod
    def reset_download_statuses_to_ready():
        for playlist in PlaylistRepository.get_all_playlists():
            playlist.download_status = "ready"
        commit_with_retries(db.session)
