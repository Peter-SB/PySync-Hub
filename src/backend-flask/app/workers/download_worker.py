import logging
import threading
import queue

from flask import Flask

from app.extensions import emit_error_message
from app.repositories.playlist_repository import PlaylistRepository
from app.services.download_services.spotify_download_service import SpotifyDownloadService
from app.services.download_services.soundcloud_download_service import SoundcloudDownloadService

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

            # Check for shutdown signal
            if playlist_id is None:
                self.download_queue.task_done()
                logger.info("Shutdown signal received. Exiting download worker.")
                break

            with self.app.app_context():
                playlist = PlaylistRepository.get_playlist_by_id(playlist_id)
                if not playlist:
                    self.download_queue.task_done()
                    continue

                logger.info(f"Downloading playlist {playlist}")

                try:
                    if playlist.platform == "spotify":
                        SpotifyDownloadService.download_playlist(playlist, self.cancellation_flags)
                    elif playlist.platform == "soundcloud":
                        SoundcloudDownloadService.download_playlist(playlist, self.cancellation_flags)
                    else:
                        error_msg = f"Unsupported platform: {playlist.platform}"
                        logger.error(error_msg)
                        emit_error_message(playlist.id, error_msg)
                        PlaylistRepository.set_download_status(playlist, 'ready')
                except Exception as e:
                    logger.error(f"Error downloading playlist {playlist.id}: {e}")
                    emit_error_message(playlist.id, f"Error downloading playlist: {str(e)}")
                    PlaylistRepository.set_download_status(playlist, 'ready')
                finally:
                    if playlist.id in self.cancellation_flags:
                        self.cancellation_flags[playlist.id].clear()

            self.download_queue.task_done()

    def add_to_queue(self, playlist_id):
        self.download_queue.put(playlist_id)

        # Set cancellation flag
        if playlist_id not in self.cancellation_flags:
            self.cancellation_flags[playlist_id] = threading.Event()
        else:
            self.cancellation_flags[playlist_id].clear()

    def add_playlists_to_queue(self, playlist_ids):
        for playlist_id in playlist_ids:
            self.add_to_queue(playlist_id)

    def cancel_download(self, playlist_id):
        logger.info(f"Playlist canceled: {playlist_id}")
        if playlist_id in self.cancellation_flags:
            self.cancellation_flags[playlist_id].set()
            logger.info(f"cancellation_flags: {self.cancellation_flags[playlist_id]}")

    def shutdown(self):
        logger.info("Shutting down DownloadManager...")
        # Queue shutdown signal
        self.download_queue.put(None)
        # Wait for the worker thread to finish its current task and exit
        self.worker_thread.join()
        logger.info("Download Manager shutdown")
