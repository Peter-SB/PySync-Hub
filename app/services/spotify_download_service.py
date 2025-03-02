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

class SpotifyDownloadService:
    @staticmethod
    def download_playlist(playlist: Playlist, cancellation_flags: dict[threading.Event]):
        """ Download all tracks in a Spotify playlist. Uses cancellation flags to stop downloads. """
        # Ensure a cancellation flag exists for this playlist.
        if playlist.id not in cancellation_flags:
            logger.info(f"Making cancellation_flags for id: {playlist.id}")
            cancellation_flags[playlist.id] = threading.Event()

        if cancellation_flags[playlist.id].is_set():
                logger.info(f"Download for playlist {playlist.name} cancelled. Cancellation flags already set. (id: {playlist.id})")
                PlaylistRepository.set_download_status(playlist, 'ready')
                return

        PlaylistRepository.set_download_status(playlist, 'downloading')

        # Iterate over the tracks and download each one.
        tracks = [pt.track for pt in playlist.tracks]
        total_tracks = len(tracks)
        for i, track in enumerate(tracks, start=1):
            if cancellation_flags[playlist.id].is_set():
                logger.info(f"Download for playlist {playlist.name} cancelled mid playlist download. (id: {playlist.id})")
                break
            try:
                SpotifyDownloadService.download_track(track)
            except Exception as e:
                logger.warning(f"Error downloading track {track.name}: {e}")

            progress_percent = int((i / total_tracks) * 100)
            PlaylistRepository.set_download_progress(playlist, progress_percent)

            time.sleep(DOWNLOAD_SLEEP_TIME)  # To reduce bot detection

        logger.info("Download Finished for Playlist '%s'", playlist.name)
        PlaylistRepository.set_download_status(playlist, 'ready')

    @staticmethod
    def download_track(track: Track):
        """ Download a single track from Spotify. """
        logger.debug(f"Download Track location: %s", track.download_location)
        
        if FileDownloadUtils.is_track_already_downloaded(track):
            return

        query = f"{track.name} {track.artist}"
        logger.info("Searching YouTube for track: '%s'", query)

        try:
            SpotifyDownloadService._download_track_with_ytdlp(track, query)

        except Exception as e:
            logger.error("Error downloading track '%s': %s", query, e, exc_info=True)
            track.notes_errors = str(e)
            db.session.add(track)
            db.session.commit()

    @staticmethod
    def _download_track_with_ytdlp(track: Track, query: str) -> None:
        """Download a track using yt-dlp and embed metadata."""
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


    @staticmethod
    def _generate_yt_dlp_options(query: str, filename: str = None):
        """Generate yt-dlp options using a sanitized filename from the YouTube title."""
        if not filename:
            filename = FileDownloadUtils.sanitize_filename(query)

        output_template = os.path.join(os.getcwd(), "downloads" ,f"{filename}.%(ext)s")  # Ensure correct filename format

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
            'quiet': False
        }

