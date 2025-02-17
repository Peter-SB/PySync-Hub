import threading
import queue
import time

from app import create_app, db
from app.models import Playlist
from app.services.spotify_download_service import SpotifyDownloadService
from flask import current_app

download_queue = queue.Queue()
cancellation_flags: dict[threading.Event] = {}


def download_worker():
    """Background worker that processes download tasks."""
    while True:
        playlist_id = download_queue.get()  # blocks until a task is available
        with current_app.app_context():
            playlist = Playlist.query.get(playlist_id)
            if not playlist:
                download_queue.task_done()
                continue

            SpotifyDownloadService.download_playlist(playlist, cancellation_flags)

        download_queue.task_done()


# Start the background worker thread (daemon=True so it ends when the app stops)
worker_thread = threading.Thread(target=download_worker, daemon=True)
worker_thread.start()
