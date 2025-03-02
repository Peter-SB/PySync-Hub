import logging
import os
import threading
import time

from yt_dlp import YoutubeDL

from app.extensions import db
from app.models import Playlist, Track
from app.repositories.playlist_repository import PlaylistRepository
from app.utils.file_download_utils import FileDownloadUtils

DOWNLOAD_SLEEP_TIME = 0.05  # To reduce bot detection

logger = logging.getLogger(__name__)


class SoundcloudDownloadService:
    @staticmethod
    def download_playlist(playlist: Playlist, cancellation_flags: dict[threading.Event]):
        """Download all tracks in a SoundCloud playlist. Uses cancellation flags to stop downloads."""
        # Ensure a cancellation flag exists for this playlist.
        if playlist.id not in cancellation_flags:
            logger.info("Creating cancellation flag for playlist id: %s", playlist.id)
            cancellation_flags[playlist.id] = threading.Event()

        if cancellation_flags[playlist.id].is_set():
            logger.info("Download for playlist '%s' cancelled. (id: %s)", playlist.name, playlist.id)
            PlaylistRepository.set_download_status(playlist, 'ready')
            return

        PlaylistRepository.set_download_status(playlist, 'downloading')

        # Iterate over the tracks and download each one.
        tracks = [pt.track for pt in playlist.tracks]
        total_tracks = len(tracks)
        for i, track in enumerate(tracks, start=1):
            if cancellation_flags[playlist.id].is_set():
                logger.info("Download for playlist '%s' cancelled mid-download. (id: %s)", playlist.name, playlist.id)
                break
            try:
                SoundcloudDownloadService.download_track(track)
            except Exception as e:
                logger.warning("Error downloading track '%s': %s", track.name, e)

            progress_percent = int((i / total_tracks) * 100)
            PlaylistRepository.set_download_progress(playlist, progress_percent)

            time.sleep(DOWNLOAD_SLEEP_TIME)  # To reduce bot detection

        logger.info("Download finished for playlist '%s'", playlist.name)
        PlaylistRepository.set_download_status(playlist, 'ready')

    @staticmethod
    def download_track(track: Track):
        """Download a single track from SoundCloud."""
        logger.debug("Download track location: %s", track.download_location)

        if FileDownloadUtils.is_track_already_downloaded(track):
            return

        # Ensure the track has a SoundCloud URL
        if not hasattr(track, 'download_url') or not track.download_url:
            logger.error("No SoundCloud URL provided for track '%s'", track.name)
            track.notes_errors = "No SoundCloud URL provided"
            db.session.add(track)
            db.session.commit()
            return

        try:
            SoundcloudDownloadService._download_track_with_ytdlp(track)
        except Exception as e:
            logger.error("Error downloading SoundCloud track '%s': %s", track.name, e, exc_info=True)
            track.notes_errors = str(e)
            db.session.add(track)
            db.session.commit()

    @staticmethod
    def _download_track_with_ytdlp(track: Track) -> None:
        """
        Download a track using yt-dlp.
        Uses the track's SoundCloud URL and saves the audio as an MP3 file.
        """
        track_title = f"{track.name}"
        sanitized_title = FileDownloadUtils.sanitize_filename(track_title)
        file_path = os.path.join(os.getcwd(), "downloads", f"{sanitized_title}.mp3")

        # Check if the track file already exists
        if os.path.exists(file_path):
            logger.info("Track '%s' already exists at '%s'. Skipping download.", track.name, file_path)
            track.download_location = file_path
            track.notes_errors = "Already Downloaded"
        else:
            ydl_opts = SoundcloudDownloadService._generate_yt_dlp_options(sanitized_title)
            with YoutubeDL(ydl_opts) as ydl:
                # Download the track from its SoundCloud URL
                ydl.download([track.download_url])
            # Embed metadata after download
            FileDownloadUtils.embed_track_metadata(file_path, track)
            track.download_location = file_path
            track.notes_errors = "Successfully Downloaded"
            logger.info("Downloaded track '%s' to '%s'", track.name, file_path)

        db.session.add(track)
        db.session.commit()

    @staticmethod
    def _generate_yt_dlp_options(filename: str) -> dict:
        """Generate yt-dlp options using a sanitized filename for a SoundCloud track."""
        output_template = os.path.join(os.getcwd(), "downloads", f"{filename}.%(ext)s")
        return {
            'format': 'bestaudio/best',
            'audioformat': 'mp3',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
        }
