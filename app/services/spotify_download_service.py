import os
import logging
import re
import threading
import time

import requests
import unicodedata
from mutagen.id3 import ID3, TIT2, TPE1, TALB, COMM, APIC
from mutagen.mp3 import MP3
from yt_dlp import YoutubeDL

from app.repositories.playlist_repository import PlaylistRepository
from config import Config
from app.models import Playlist, Track
from pytubefix import YouTube, Search
from app.extensions import db, socketio

logger = logging.getLogger(__name__)

class SpotifyDownloadService:

    @staticmethod
    def _sanitize_filename(s: str, max_length: int = 255) -> str:
        """Sanitize a string making it safe to use as a filename."""
        pattern = r'[^\w\-_\. ]'  # This keeps letters, digits, underscore, hyphen, dot, and space.
        regex = re.compile(pattern, re.UNICODE)
        filename = regex.sub("", s)

        # Truncate to max_length and remove trailing spaces
        return filename[:max_length].rstrip()

    @staticmethod
    def download_playlist(playlist: Playlist, cancellation_flags: dict[threading.Event]):
        # Ensure a cancellation flag exists for this playlist.
        if playlist.id not in cancellation_flags:
            cancellation_flags[playlist.id] = threading.Event()

        PlaylistRepository.set_download_status(playlist, 'downloading')

        socketio.emit("download_status", {"id": playlist.id, "status": "downloading", "progress": 0})

        # Iterate over the tracks and download each one.
        tracks = [pt.track for pt in playlist.tracks]
        total_tracks = len(tracks)
        for i, track in enumerate(tracks, start=1):
            # Check if cancellation has been requested.
            if cancellation_flags[playlist.id].is_set():
                print(f"Download for playlist {playlist.name} cancelled. (id: {playlist.id})")
                break

            try:
                SpotifyDownloadService.download_track(track)
            except Exception as e:
                print(f"Error downloading track {track.name}: {e}")

            progress_percent = int((i / total_tracks) * 100)
            socketio.emit("download_status", {
                "id": playlist.id,
                "status": "downloading",
                "progress": progress_percent
            })
            PlaylistRepository.set_download_progress(playlist, progress_percent)

            time.sleep(0.05)  # To reduce bot detection

        # After finishing (or if cancelled) update status back to 'ready'
        logger.info("Download Finished for Playlist '%s'", playlist.name)
        PlaylistRepository.set_download_status(playlist, 'ready')
        socketio.emit("download_status", {"id": playlist.id, "status": "ready"})

        # Clear the cancellation flag for future downloads.
        cancellation_flags[playlist.id].clear()

    @staticmethod
    def download_track(track: Track):
        logger.info(f"Download Track location: {track.download_location}")
        if track.download_location and os.path.isfile(track.download_location):
            logger.info("Track '%s' already downloaded, skipping.", track.name)
            track.notes_errors = "Already Downloaded, Skipped"
            db.session.add(track)
            db.session.commit()
            return

        query = f"{track.name} {track.artist}"
        logger.info("Searching YouTube for track: '%s'", query)

        try:
            with YoutubeDL(SpotifyDownloadService._generate_yt_dlp_options(query)) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)

                if 'entries' in info:
                    video_info = info['entries'][0]
                else:
                    video_info = info

                # Extract YouTube video title
                youtube_title = video_info.get('title', f"{track.name} {track.artist}")
                sanitized_title = SpotifyDownloadService._sanitize_filename(youtube_title)

                # Set output filename for download
                file_path = os.path.join(os.getcwd(), "downloads", f"{sanitized_title}.mp3")

                if os.path.exists(file_path):
                    logger.info("Track '%s' already exists at '%s'. Skipping download.", track.name, file_path)
                    track.download_location = file_path
                    track.notes_errors = "Already Downloaded"
                else:
                    # Download using the sanitized YouTube title
                    ydl_opts = SpotifyDownloadService._generate_yt_dlp_options(query, sanitized_title)
                    with YoutubeDL(ydl_opts) as ydl:
                        ydl.extract_info(f"ytsearch:{query}", download=True)

                    SpotifyDownloadService._embed_track_metadata(file_path, track)

                    track.download_location = file_path
                    track.notes_errors = "Successfully Downloaded"
                    logger.info("Downloaded track '%s' to '%s'", track.name, file_path)

                db.session.add(track)
                db.session.commit()
                logger.info("Downloaded track '%s' to '%s'", track.name, file_path)

        except Exception as e:
            logger.error("Error downloading track '%s': %s", query, e, exc_info=True)
            track.notes_errors = str(e)
            db.session.add(track)
            db.session.commit()

    @staticmethod
    def _generate_yt_dlp_options(query: str, filename: str = None):
        """Generate yt-dlp options using a sanitized filename from the YouTube title."""
        if not filename:
            filename = SpotifyDownloadService._sanitize_filename(query)

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
                'preferredcodec': 'mp3',  # Change to 'aac', 'flac', 'wav', 'alac' as needed
                'preferredquality': '192',  # Bitrate for MP3/AAC
            }],
            'quiet': False
        }


    @staticmethod
    def _embed_track_metadata(file_path, track: Track):
        """
        Adds metadata from the Spotify track data to the MP3 audio file, including cover art if available.

        :param track: Track data from Spotify.
        :param track_file_path: Path to the MP3 audio file.
        """
        audio = MP3(file_path, ID3=ID3)


        track_name = track.name
        track_artist = track.artist
        #track_artists = ", ".join([artist["name"] for artist in track_data["artists"]])
        #track_popularity = track_data["popularity"]
        track_album = track.album
        track_cover_imgs = track.album_art_url

        # Basic metadata
        audio['TIT2'] = TIT2(encoding=3, text=track_name)
        audio['TPE1'] = TPE1(encoding=3, text=track_artist)
        audio['TALB'] = TALB(encoding=3, text=track_album)
        #audio['COMM'] = COMM(encoding=3, lang='eng', desc=f'Popularity = {track_popularity}',
        #                     text=f"{track_popularity}")  # todo: Needs fixing

        audio.save()

        audio = ID3(file_path)

        # Adding cover art
        if track_cover_imgs:
            response = requests.get(track_cover_imgs)
            logger.info(f"Track image: {track_cover_imgs}, response {response.status_code}")
            if response.status_code == 200:
                audio['APIC'] = APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # Cover image
                    desc=u'Cover',
                    data=response.content
                )

        audio.save()

