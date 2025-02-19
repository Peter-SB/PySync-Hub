# app/services/playlist_sync_service.py
from datetime import datetime
from typing import List, Optional

import logging

from spotipy import SpotifyException

from app.extensions import db
from app.models import Playlist
from app.repositories.playlist_repository import PlaylistRepository
from app.services.spotify_service import SpotifyService
from app.services.track_manager_service import TrackManagerService

logger = logging.getLogger(__name__)


class PlaylistManagerService:

    @staticmethod
    def refresh_playlists(playlists: list[Playlist]) -> List[Playlist]:
        """
        Sync playlists from external platform (e.g., Spotify).

        If selected_ids is provided, only those playlists are synced.
        Otherwise, all playlists are synced.

        :param selected_ids: Optional list of playlist IDs to sync.
        :return: List of playlists that were processed.
        """

        for playlist in playlists:
            if playlist.platform == 'spotify':
                try:
                    data = SpotifyService.get_playlist_data(playlist.external_id)
                    playlist.name = data['name']
                    playlist.last_synced = datetime.utcnow()
                    playlist.image_url = data['image_url']
                    playlist.track_count = data['track_count']
                    logger.info("Pulled latest playlist info (ID: %s, external_id: %s)", playlist.id,
                                playlist.external_id)

                    TrackManagerService.fetch_playlist_tracks(playlist.id)

                except Exception as e:
                    logger.error("Failed to sync playlist ID %s: %s", playlist.id, e, exc_info=True)

        try:
            db.session.commit()
            logger.info("Database commit successful after syncing playlists")
        except Exception as e:
            logger.error("Database commit failed during sync: %s", e, exc_info=True)
            db.session.rollback()

        return playlists

    @staticmethod
    def add_playlists(url_or_id) -> Optional[str]:
        logger.info("Attempting to add playlist with url_or_id: %s", url_or_id)
        platform = 'spotify'  # Will be extended for SoundCloud

        if not url_or_id:
            logger.info("No url_or_id found: %s", url_or_id)
            return "No URL or ID Detected"

        try:
            playlist_data = SpotifyService.get_playlist_data(url_or_id)
            logger.debug("Fetched playlist data: %s", playlist_data)

            existing = Playlist.query.filter_by(
                external_id=playlist_data['external_id'],
                platform=platform
            ).first()

            if existing:
                logger.info("Playlist already exists with external_id: %s", playlist_data['external_id'])
                return "Playlist Already Exists"
            else:
                playlist = Playlist(
                    name=playlist_data['name'],
                    platform=platform,
                    external_id=playlist_data['external_id'],
                    image_url=playlist_data['image_url'],
                    track_count=playlist_data['track_count'],
                    url=playlist_data['url'],
                    download_status="ready"
                )
                db.session.add(playlist)
                db.session.commit()
                logger.info("Added new playlist with external_id: %s", playlist_data['external_id'])
        except SpotifyException as e:
            if e.http_status == 404:
                logger.error("Playlist not found for url_or_id: %s", url_or_id)
                return "Playlist not found. Please try another URL or ID."
            logger.error(f"Spotify Error: {e.http_status}. Try a different Playlist")
            return "There was a Spotify Error."

        except Exception as e:
            logger.error("Error adding playlist with url_or_id '%s': %s (%s)", url_or_id, e, type(e), exc_info=True)
            # Optionally, handle the error further (e.g., flash a message or return an error response)

    @staticmethod
    def delete_playlists(selected_ids):
        logger.info("Deleting playlists with IDs: %s", selected_ids)

        if selected_ids:
            try:
                selected_ids_int = [int(pid) for pid in selected_ids]
            except ValueError as ve:
                logger.error("Invalid playlist ID format in selected_ids: %s", selected_ids)
                selected_ids_int = []

            try:
                # Bulk delete; synchronize_session=False for performance since we don't need the session updates
                Playlist.query.filter(Playlist.id.in_(selected_ids_int)).delete(synchronize_session=False)
                db.session.commit()
                logger.info("Deleted playlists with IDs: %s", selected_ids_int)
            except Exception as e:
                logger.error("Error deleting playlists with IDs %s: %s", selected_ids_int, e, exc_info=True)
