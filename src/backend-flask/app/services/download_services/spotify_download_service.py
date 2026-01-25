import logging
import os

from yt_dlp import YoutubeDL

from app.extensions import db
from app.models import Track, Playlist
from app.services.download_services.base_download_service import BaseDownloadService
from app.utils.file_download_utils import FileDownloadUtils
from app.utils.db_utils import commit_with_retries
from config import Config

logger = logging.getLogger(__name__)


class SpotifyDownloadService(BaseDownloadService):
    @classmethod
    def download_track_with_ytdlp(cls, track: Track, playlist: Playlist = None) -> None:
        """Download a track using yt-dlp and embed metadata.

        First checks if a download URL is already stored in the database.
        If one is found, it uses that URL; otherwise, it searches YouTube.
        """
        # Determine the query string for options (even if URL exists)
        query = f"{track.name} {track.artist}"

        sanitized_title, url_to_use = cls._determine_download_details(query, track)
        
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
            ydl_opts = SpotifyDownloadService._generate_yt_dlp_options(query, filename, subfolder)
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url_to_use])

            FileDownloadUtils.embed_track_metadata(file_path, track)
            track.set_download_location(file_path)
            logger.info("Downloaded track '%s' to '%s'", track.name, file_path)

        db.session.add(track)
        commit_with_retries(db.session)
        logger.info("Processed track '%s' with file '%s'", track.name, file_path)

    @classmethod
    def _determine_download_details(cls, query, track):
        """Determine the download URL and the file name

        :param query: The query string to search for
        :param track: The track object to use
        :return: The sanitized title (filename) and the URL to use
        """
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
