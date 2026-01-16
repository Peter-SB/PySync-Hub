import logging
import os

from yt_dlp import YoutubeDL

from app.extensions import db
from app.models import Track
from app.services.download_services.base_download_service import BaseDownloadService
from app.utils.file_download_utils import FileDownloadUtils
from app.utils.db_utils import commit_with_retries
from config import Config

logger = logging.getLogger(__name__)


class YouTubeDownloadService(BaseDownloadService):
    """
    Service for downloading YouTube tracks using yt-dlp.
    
    Uses the base _generate_yt_dlp_options method since YouTube downloads work
    well with the standard options. The base method already configures:
    - bestaudio format selection
    - FFmpeg audio extraction to MP3
    - Proper output templates
    Unlike Spotify, YouTube URLs don't require searching, so no override needed.
    """

    @classmethod
    def download_track_with_ytdlp(cls, track: Track) -> None:
        """
        Download a YouTube video as audio using yt-dlp.
        
        :param track: Track object containing YouTube video URL
        """
        if not hasattr(track, 'download_url') or not track.download_url:
            logger.error("No YouTube URL provided for track '%s'", track.name)
            track.notes_errors = "No YouTube URL provided"
            db.session.add(track)
            commit_with_retries(db.session)
            return

        track_title = f"{track.name} - {track.artist}"
        sanitized_title = FileDownloadUtils.sanitize_filename(track_title)
        file_path = os.path.join(Config.DOWNLOAD_FOLDER, f"{sanitized_title}.mp3")

        if os.path.exists(file_path):
            logger.info("Track '%s' already exists at '%s'. Skipping download.", track.name, file_path)
            track.set_download_location(file_path)
        else:
            ydl_opts = YouTubeDownloadService._generate_yt_dlp_options(track_title, sanitized_title)
            
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    logger.info("Downloading track '%s' from YouTube URL: %s", track.name, track.download_url)
                    ydl.download([track.download_url])

                FileDownloadUtils.embed_track_metadata(file_path, track)
                track.set_download_location(file_path)
                logger.info("Downloaded track '%s' to '%s'", track.name, file_path)
                
            except Exception as e:
                logger.error("Error downloading YouTube track '%s': %s", track.name, e)
                track.notes_errors = f"Download failed: {str(e)}"
                db.session.add(track)
                commit_with_retries(db.session)
                raise

        db.session.add(track)
        commit_with_retries(db.session)
