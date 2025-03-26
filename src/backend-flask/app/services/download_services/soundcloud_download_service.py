import logging
import os

from yt_dlp import YoutubeDL

from app.extensions import db
from app.models import Track
from app.services.download_services.base_download_service import BaseDownloadService
from app.utils.file_download_utils import FileDownloadUtils

DOWNLOAD_SLEEP_TIME = 0.05  # To reduce bot detection

logger = logging.getLogger(__name__)


class SoundcloudDownloadService(BaseDownloadService):
    @classmethod
    def download_track_with_ytdlp(cls, track: Track) -> None:
        """
        Download a track using yt-dlp.
        Uses the track's SoundCloud URL and saves the audio as an MP3 file.
        """
        if not hasattr(track, 'download_url') or not track.download_url:
            logger.error("No SoundCloud URL provided for track '%s'", track.name)
            track.notes_errors = "No SoundCloud URL provided"
            db.session.add(track)
            db.session.commit()
            return

        track_title = f"{track.name}"
        sanitized_title = FileDownloadUtils.sanitize_filename(track_title)
        file_path = os.path.join(os.getcwd(), "downloads", f"{sanitized_title}.mp3")

        if os.path.exists(file_path):
            logger.info("Track '%s' already exists at '%s'. Skipping download.", track.name, file_path)
            track.download_location = file_path

        else:
            ydl_opts = SoundcloudDownloadService._generate_yt_dlp_options(sanitized_title)
            with YoutubeDL(ydl_opts) as ydl:
                # Download the track from its SoundCloud URL
                ydl.download([track.download_url])

            FileDownloadUtils.embed_track_metadata(file_path, track)

            track.download_location = file_path
            logger.info("Downloaded track '%s' to '%s'", track.name, file_path)

        db.session.add(track)
        db.session.commit()
