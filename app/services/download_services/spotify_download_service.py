import logging
import os

from yt_dlp import YoutubeDL

from app.extensions import db
from app.models import Track
from app.services.download_services.base_download_service import BaseDownloadService
from app.utils.file_download_utils import FileDownloadUtils
from app.config import Config

logger = logging.getLogger(__name__)


class SpotifyDownloadService(BaseDownloadService):
    @classmethod
    def download_track_with_ytdlp(cls, track: Track) -> None:
        """Download a track using yt-dlp and embed metadata.

        First checks if a download URL is already stored in the database.
        If one is found, it uses that URL; otherwise, it searches YouTube.
        """
        # Determine the query string for options (even if URL exists)
        query = f"{track.name} {track.artist}"

        sanitized_title, url_to_use = cls.method_name(query, track)

        file_path = os.path.join(os.getcwd(), Config.DOWNLOAD_FOLDER, f"{sanitized_title}.mp3")

        # Check if the file already exists to avoid duplicate downloads
        if os.path.exists(file_path):
            logger.info("Track '%s' already exists at '%s'. Skipping download.", track.name, file_path)
            track.download_location = file_path
            # track.notes_errors = "Already Downloaded, Skipped"
        else:
            # Download using the determined URL
            ydl_opts = SpotifyDownloadService._generate_yt_dlp_options(query, sanitized_title)
            with YoutubeDL(ydl_opts) as ydl:
                # Note: We pass a list with the URL to download directly
                ydl.download([url_to_use])
            # Embed metadata after download
            FileDownloadUtils.embed_track_metadata(file_path, track)
            track.download_location = file_path
            #track.notes_errors = "Successfully Downloaded"
            logger.info("Downloaded track '%s' to '%s'", track.name, file_path)

        db.session.add(track)
        db.session.commit()
        logger.info("Processed track '%s' with file '%s'", track.name, file_path)

    @classmethod
    def method_name(cls, query, track):
        """Determine the download URL to use for a track a"""
        if track.download_url:
            url_to_use = track.download_url
            logger.info("Using pre-existing download URL for track '%s'", track.name)
            # Extract video information from the existing URL
            with YoutubeDL(SpotifyDownloadService._generate_yt_dlp_options(query)) as ydl:
                video_info = ydl.extract_info(url_to_use, download=False)
                youtube_title = video_info.get('title', query)
                sanitized_title = FileDownloadUtils.sanitize_filename(youtube_title)
        else:
            logger.info("No download URL in DB. Searching YouTube for track: '%s'", query)
            with YoutubeDL(SpotifyDownloadService._generate_yt_dlp_options(query)) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)
                if 'entries' in info and len(info['entries']) > 0:
                    video_info = info['entries'][0]
                else:
                    video_info = info
                youtube_title = video_info.get('title', query)
                sanitized_title = FileDownloadUtils.sanitize_filename(youtube_title)
                url_to_use = video_info.get('webpage_url')
                # Save the found URL into the DB for future use
                track.download_url = url_to_use
        return sanitized_title, url_to_use