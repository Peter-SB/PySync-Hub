import threading
import queue
import time
from app.services.spotify_download_service import SpotifyDownloadService

task_queue = queue.Queue()

def worker():
    while True:
        task = task_queue.get()
        if task is None:
            break

        playlist_id = task["playlist_id"]
        SpotifyDownloadService.download_tracks_for_playlist(playlist_id)
        task_queue.task_done()

worker_thread = threading.Thread(target=worker, daemon=True)
worker_thread.start()