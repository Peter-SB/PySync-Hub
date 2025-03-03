import logging
import threading
import queue

from app.repositories.playlist_repository import PlaylistRepository
from app.services.download_services.soundcloud_download_service import SoundcloudDownloadService
from app.services.download_services.spotify_download_service import SpotifyDownloadService
from flask import Flask

logger = logging.getLogger(__name__)


class DownloadManager:
    def __init__(self, app: Flask):
        logger.info("Initialising Download Manager")
        self.download_queue = queue.Queue()
        self.cancellation_flags: dict[threading.Event] = {}
        self.app = app

        # Start the background worker thread (daemon=True so it ends when the app stops)
        self.worker_thread = threading.Thread(target=self._download_worker, daemon=True)
        self.worker_thread.start()

        logger.info("Download Manager Initialised")


    def _download_worker(self):
        """ Background worker that processes the download queue. """
        logger.info("Download Worker Started")
        while True:
            playlist_id = self.download_queue.get()  # blocks until a task is available
            with self.app.app_context():
                playlist = PlaylistRepository.get_playlist_by_id(playlist_id)
                if not playlist:
                    self.download_queue.task_done()
                    continue

                logger.info(f"Downloading playlist {playlist}")

                if playlist.platform == "spotify":
                    SpotifyDownloadService.download_playlist(playlist, self.cancellation_flags)
                elif playlist.platform == "soundcloud":
                    SoundcloudDownloadService.download_playlist(playlist, self.cancellation_flags)

                self.cancellation_flags[playlist.id].clear()
                logger.info(f"cancellation_flags: {self.cancellation_flags}")

            self.download_queue.task_done()

    def add_to_queue(self, playlist_id):
        self.download_queue.put(playlist_id)

    def add_playlists_to_queue(self, playlist_ids):
        for playlist_id in playlist_ids:
            self.add_to_queue(playlist_id)

    def cancel_download(self, playlist_id):
        """ todo: Fix cancel button"""
        logger.info(f"Playlist canceled: {playlist_id}")
        if playlist_id in self.cancellation_flags:
            self.cancellation_flags[playlist_id].set()
            logger.info(f"cancellation_flags: {self.cancellation_flags[playlist_id]}")


