import logging
import os

from yt_dlp import YoutubeDL

from app.extensions import db
from app.models import Track
from app.services.download_services.base_download_service import BaseDownloadService
from app.utils.file_download_utils import FileDownloadUtils

DOWNLOAD_SLEEP_TIME = 0.05  # To reduce bot detection

logger = logging.getLogger(__name__)


class SpotifyDownloadService(BaseDownloadService):
    @classmethod
    def download_track_with_ytdlp(cls, track: Track) -> None:
        """Download a track using yt-dlp and embed metadata."""
        query = f"{track.name} {track.artist}"
        logger.info("Searching YouTube for track: '%s'", query)

        with YoutubeDL(SpotifyDownloadService._generate_yt_dlp_options(query)) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)

            if 'entries' in info:
                video_info = info['entries'][0]
            else:
                video_info = info

            # Extract YouTube video title
            youtube_title = video_info.get('title', f"{track.name} {track.artist}")
            sanitized_title = FileDownloadUtils.sanitize_filename(youtube_title)

            # Set output filename for download
            file_path = os.path.join(os.getcwd(), "downloads", f"{sanitized_title}.mp3")

            # Check if the track already exists
            if os.path.exists(file_path):
                logger.info("Track '%s' already exists at '%s'. Skipping download.", track.name, file_path)
                track.download_location = file_path
                track.notes_errors = "Already Downloaded"
            else:
                # Download using the sanitized YouTube title
                ydl_opts = SpotifyDownloadService._generate_yt_dlp_options(query, sanitized_title)
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(f"ytsearch:{query}", download=True)

                FileDownloadUtils.embed_track_metadata(file_path, track)

                track.download_location = file_path
                track.notes_errors = "Successfully Downloaded"
                logger.info("Downloaded track '%s' to '%s'", track.name, file_path)

            db.session.add(track)
            db.session.commit()
            logger.info("Downloaded track '%s' to '%s'", track.name, file_path)
