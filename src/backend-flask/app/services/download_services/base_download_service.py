import logging
import os
import platform
import sys
import threading
import time
from abc import ABC, abstractmethod

from yt_dlp import YoutubeDL

from app.extensions import db, emit_error_message
from app.models import Playlist, Track
from app.repositories.playlist_repository import PlaylistRepository
from app.utils.file_download_utils import FileDownloadUtils
from config import Config

DOWNLOAD_SLEEP_TIME = 0.05  # To reduce bot detection
logger = logging.getLogger(__name__)


class BaseDownloadService(ABC):
    DOWNLOAD_SLEEP_TIME = DOWNLOAD_SLEEP_TIME

    @classmethod
    def download_playlist(cls, playlist: Playlist, cancellation_flags: dict[threading.Event]):
        """
        Common implementation for downloading a playlist.
        It handles cancellation flags, status updates, progress tracking,
        and then calls the subclass-specific download_track for each track.
        """
        try:
            if playlist.id not in cancellation_flags:
                logger.info("Creating cancellation flag for playlist id: %s", playlist.id)
                cancellation_flags[playlist.id] = threading.Event()

            if cancellation_flags[playlist.id].is_set():
                logger.info("Download for playlist '%s' cancelled. (id: %s)", playlist.name, playlist.id)
                PlaylistRepository.set_download_status(playlist, 'ready')
                return

            PlaylistRepository.set_download_status(playlist, 'downloading')
            tracks = [pt.track for pt in playlist.tracks]
            total_tracks = len(tracks)

            for i, track in enumerate(tracks, start=1):
                if cancellation_flags[playlist.id].is_set():
                    logger.info("Download for playlist '%s' cancelled mid-download. (id: %s)",
                                playlist.name, playlist.id)
                    break

                try:
                    cls.download_track(track)
                except Exception as e:
                    logger.warning("Error downloading track '%s': %s", track.name, e)
                    error_message = f"Error downloading playlist '{playlist.name}': {str(e)}"
                    emit_error_message( "" , error_message)
                progress_percent = int((i / total_tracks) * 100)
                PlaylistRepository.set_download_progress(playlist, progress_percent)
                time.sleep(cls.DOWNLOAD_SLEEP_TIME)

            logger.info("Download finished for playlist '%s'", playlist.name)
            PlaylistRepository.set_download_status(playlist, 'ready')
        except Exception as e:
            logger.error("Error downloading playlist '%s': %s", playlist.name, e)
            error_message = f"Error downloading playlist '{playlist.name}': {str(e)}"
            emit_error_message(playlist.id, error_message)
            PlaylistRepository.set_download_status(playlist, 'ready')
            raise e

    @classmethod
    def download_track(cls, track: Track):
        """ Download a single track. """
        logger.debug(f"Download Track location: %s", track.download_location)

        track.notes_errors = ""
        db.session.add(track)
        db.session.commit()

        if track.is_downloaded():
            logger.info("Track '%s' already downloaded, skipping.", track.name)
            return

        try:
            cls.download_track_with_ytdlp(track)
        except Exception as e:
            logger.error("Error downloading track '%s - %s`: %s", track.name, track.artist, e, exc_info=True)
            track.notes_errors = str(e)
            db.session.add(track)
            db.session.commit()
            # todo: display frontend error            
            raise e

    @classmethod
    def _generate_yt_dlp_options(cls, query: str, filename: str = None):
        """Generate yt-dlp options using a sanitized filename from the YouTube title."""
        if not filename:
            filename = FileDownloadUtils.sanitize_filename(query)

        output_template = os.path.join(
                                       Config.DOWNLOAD_FOLDER,
                                       f"{filename}.%(ext)s")  # Ensure correct filename format

        return {
            'format': 'bestaudio/best',
            'audioformat': 'mp3',
            'extractaudio': True,
            'nocheckcertificate': True,
            'outtmpl': output_template,  # Set output file name
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',  # Bitrate for MP3/AAC
            }],
            'ffmpeg_location': cls.get_ffmpeg_location(),
            'quiet': False
        }

    @classmethod
    @abstractmethod
    def download_track_with_ytdlp(cls, track: Track) -> None:
        """Handle the actual yt-dlp download logic."""
        pass

    @classmethod
    def get_ffmpeg_location(cls):
        """Returns the appropriate FFmpeg binary location depending on the OS."""
        ffmpeg_name = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"

        # If running inside an Electron app, determine app location
        if getattr(sys, 'frozen', False):  # Running as a packaged app (PyInstaller)
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))  # Dev mode

        # Possible locations
        possible_paths = [
            os.path.join(Config.FFMPEG_FOLDER, ffmpeg_name),
            "/ffmpeg/ffmpeg",
            os.path.join(base_path, "ffmpeg", ffmpeg_name),  # App bundle path
            os.path.join(base_path, ffmpeg_name),  # Directly in app folder
            os.path.join(os.getcwd(), ffmpeg_name),  # In current working directory
            os.path.join(os.getcwd(), "ffmpeg", ffmpeg_name)  # In 'ffmpeg' subfolder
        ]

        # Check if any of the paths exist
        for path in possible_paths:
            if os.path.isfile(path):
                logger.info("Found FFmpeg at: %s", path)
                return path

        # Fallback: Check system PATH

        print(possible_paths)
        logger.info("FFmepg Path Not Found. Check ffmpeg folder. Falling back to search for global FFmpeg")
        return ffmpeg_name  # Allows the system to find FFmpeg if installed globally

