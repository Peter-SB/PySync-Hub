import logging
import os

from yt_dlp import YoutubeDL

from app.extensions import db
from app.models import Track, Playlist
from app.services.download_services.base_download_service import BaseDownloadService
from app.utils.file_download_utils import FileDownloadUtils
from app.utils.db_utils import commit_with_retries
from config import Config

DOWNLOAD_SLEEP_TIME = 0.05  # To reduce bot detection

logger = logging.getLogger(__name__)


class SoundcloudDownloadService(BaseDownloadService):
    @classmethod
    def download_track_with_ytdlp(cls, track: Track, playlist: Playlist = None) -> None:
        """
        Download a track using yt-dlp.
        Uses the track's SoundCloud URL and saves the audio as an MP3 file.
        """
        if not hasattr(track, 'download_url') or not track.download_url:
            logger.error("No SoundCloud URL provided for track '%s'", track.name)
            track.notes_errors = "No SoundCloud URL provided"
            db.session.add(track)
            commit_with_retries(db.session)
            return

        track_title = f"{track.name}"
        sanitized_title = FileDownloadUtils.sanitize_filename(track_title)
        
        # Get the download path based on current pattern
        subfolder, filename = FileDownloadUtils.get_download_path_for_track(track, playlist)
        
        # Construct the full file path
        if subfolder:
            os.makedirs(os.path.join(Config.DOWNLOAD_FOLDER, subfolder), exist_ok=True)
            file_path = os.path.join(Config.DOWNLOAD_FOLDER, subfolder, f"{filename}.mp3")
        else:
            file_path = os.path.join(Config.DOWNLOAD_FOLDER, f"{filename}.mp3")

        if os.path.exists(file_path):
            logger.info("Track '%s' already exists at '%s'. Skipping download.", track.name, file_path)
            track.set_download_location(file_path)

        else:
            ydl_opts = SoundcloudDownloadService._generate_yt_dlp_options(sanitized_title, filename, subfolder)
            with YoutubeDL(ydl_opts) as ydl:
                # Download the track from its SoundCloud URL
                logger.info("Downloading track '%s' from SoundCloud URL: %s", track.name, track.download_url)
                logger.info("yt-dlp options: %s", ydl_opts)
                ydl.download([track.download_url])

            FileDownloadUtils.embed_track_metadata(file_path, track)

            track.set_download_location(file_path)
            logger.info("Downloaded track '%s' to '%s'", track.name, file_path)

        db.session.add(track)
        commit_with_retries(db.session)
