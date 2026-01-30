# app/services/playlist_sync_service.py
from datetime import datetime
from typing import List, Optional

import logging

from app.extensions import db, emit_playlist_sync_update
from app.models import Playlist
from app.repositories.playlist_repository import PlaylistRepository
from app.services.platform_services.platform_services_factory import PlatformServiceFactory
from app.services.platform_services.soundcloud_service import SoundcloudService
from app.services.track_manager_service import TrackManagerService
from app.utils.db_utils import commit_with_retries

logger = logging.getLogger(__name__)


class PlaylistManagerService:

    @staticmethod
    def sync_playlists(playlists: list[Playlist]) -> List[Playlist]:
        """
        Sync (but not downloads) playlists from external platform (e.g. Spotify, Souncloud).

        If selected_ids is provided, only those playlists are synced.
        Otherwise, all playlists are synced.

        :param playlists: List of Playlist objects to sync.
        :return: List of playlists that were processed.
        """
        for playlist in playlists:
            try:
                data = PlatformServiceFactory.get_service(playlist.platform).get_playlist_data(playlist.url)
                playlist.name = data['name']
                playlist.last_synced = datetime.utcnow()
                playlist.image_url = data['image_url']
                playlist.track_count = data['track_count']                
                logger.info("Pulled latest playlist info (ID: %s, external_id: %s)", playlist.id, playlist.external_id)
                            
                TrackManagerService.fetch_playlist_tracks(playlist.id) # todo: investigate if this make duplicate calls with get_playlist_data
                
                # Get updated tracks after fetching
                tracks = PlaylistRepository.get_playlist_tracks(playlist.id)
                
                # Emit WebSocket event to update the frontend with track count and tracks
                emit_playlist_sync_update(playlist.id, data['track_count'], tracks)

            except Exception as e:
                logger.error("Failed to sync playlist ID %s: %s", playlist.id, e, exc_info=True)

        try:
            commit_with_retries(db.session)
            logger.info("Database commit successful after syncing playlists")
        except Exception as e:
            logger.error("Database commit failed during sync: %s", e, exc_info=True)
            db.session.rollback()

        return playlists

    @staticmethod
    def add_playlists(playlist_url: str, date_limit=None, track_limit=None) -> Optional[str]:
        """ Add a new playlist from a platform url.
        :return: Error sting or None if successful"""

        logger.info("Attempting to add playlist with url_or_id: %s", playlist_url)

        if not playlist_url:
            logger.info("No url_or_id found: %s", playlist_url)
            return "No URL or ID Detected"
        try:
            musicPlatformService = PlatformServiceFactory.get_service_by_url(playlist_url)
            playlist_data = musicPlatformService.get_playlist_data(playlist_url)

        except Exception as e:
            logger.error("Error fetching playlist data for URL %s: %s", playlist_url, e, exc_info=True)
            if "404" in str(e):
                return "Playlist not found. Please check the playlist is public or try another URL."

            return f"Error Adding Playlist: {e}"

        logger.debug("Fetched playlist data: %s", playlist_data)

        existing = Playlist.query.filter_by(
            external_id=playlist_data['external_id'],
            platform=playlist_data['platform']
        ).first()

        if existing:
            logger.info("Playlist already exists with external_id: %s", playlist_data['external_id'])
            return "Playlist Already Added"

        playlist = PlaylistRepository.create_playlist(playlist_data)
        playlist.track_limit = int(track_limit) if track_limit else None
        playlist.date_limit = datetime.strptime(date_limit, '%Y-%m-%d').date() if date_limit else None

        try:
            TrackManagerService.fetch_playlist_tracks(playlist.id)
        except Exception as e:
            logger.error("Error fetching tracks for new playlist: %s", e, exc_info=True)
            return str(e)

        return None

    @staticmethod
    def delete_playlists(selected_ids: List[int]) -> None:
        """ todo: Move to PlaylistRepository """
        logger.info("Deleting playlists with IDs: %s", selected_ids)

        if selected_ids:
            try:
                selected_ids_int = [int(pid) for pid in selected_ids]
            except ValueError as ve:
                logger.error("Invalid playlist ID format in selected_ids: %s", selected_ids)
                selected_ids_int = []

            try:
                PlaylistRepository.delete_playlists_by_ids(selected_ids_int)
                logger.info("Deleted playlists with IDs: %s", selected_ids_int)
            except Exception as e:
                logger.error("Error deleting playlists with IDs %s: %s", selected_ids_int, e, exc_info=True)

    @staticmethod
    def emit_playlist_sync_with_tracks(playlist_id, track_count):
        """
        Helper method to emit playlist sync updates with tracks via WebSocket.
        This is called after syncing a playlist to update the frontend.
        """
        try:
            # Get updated tracks
            tracks = PlaylistRepository.get_playlist_tracks(playlist_id)
            
            # Emit WebSocket event to update the frontend with track count and tracks
            emit_playlist_sync_update(playlist_id, track_count, tracks)
            logger.info("Emitted playlist sync update with tracks for playlist ID %s", playlist_id)
        except Exception as e:
            logger.error("Failed to emit playlist sync update with tracks: %s", e, exc_info=True)
