import os
import logging
import threading
import time

import requests
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

            time.sleep(0.005)  # To reduce bot detection

        # After finishing (or if cancelled) update status back to 'ready'
        logger.info("Download Finished for Playlist '%s'", playlist.name)
        PlaylistRepository.set_download_status(playlist, 'ready')
        socketio.emit("download_status", {"id": playlist.id, "status": "ready"})

        # Clear the cancellation flag for future downloads.
        cancellation_flags[playlist.id].clear()

    @staticmethod
    def download_track_pytube(track: Track):
        logger.info(f"Download Track location: {track.download_location}")
        if track.download_location and os.path.isfile(track.download_location):
            logger.info("Track '%s' already downloaded, skipping.", track.name)
            track.notes_errors = "Already Downloaded, Skipped"
            db.session.add(track)
            db.session.commit()
            return

        # Build a search query combining the track name and artist
        query = f"{track.name} {track.artist}"
        logger.info("Searching YouTube for track: '%s'", query)
        try:
            # Perform a YouTube search using pytube's Search class
            search = Search(query)
            if not search.videos:
                error_msg = f"No YouTube results found for track: '{query}'"
                logger.error(error_msg)
                track.notes_errors = error_msg
                db.session.add(track)
                db.session.commit()
                return

            # Pick the first result
            video = search.videos[0]
            video_url = video.watch_url
            track.download_url = video_url
            logger.info("Found YouTube video URL '%s' for track: '%s'", video_url, query)

            # Create a YouTube object to access streams
            yt = YouTube(video_url, "WEB")
            # Choose an audio-only stream – ordering by bitrate (highest first)
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if not audio_stream:
                error_msg = f"No AAC audio stream available for video: '{video_url}'"
                logger.error(error_msg)
                track.notes_errors = error_msg
                db.session.add(track)
                db.session.commit()
                return

            # Download the audio stream to the specified download folder
            logger.info("Downloading track '%s'...", track.name)
            file_path = audio_stream.download(output_path=Config.DOWNLOAD_FOLDER)
            logger.info("Downloaded '%s' to '%s'", track.name, file_path)

            # Rename to .aac for compatibility
            aac_file_path = os.path.splitext(file_path)[0] + ".aac"
            os.rename(file_path, aac_file_path)
            logger.info("Renamed '%s' to '%s'", file_path, aac_file_path)

            # Update the track record with the downloaded file location
            track.download_location = file_path
            db.session.add(track)
            db.session.commit()

        except Exception as e:
            logger.error("Error downloading track '%s': %s", query, e, exc_info=True)
            track.notes_errors = str(e)
            db.session.add(track)
            db.session.commit()

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
            ydl_opts = {
                'format': 'bestaudio/best',
                'audioformat': 'mp3',
                'extractaudio': True,
                'nocheckcertificate': True,
                'outtmpl': os.path.join(Config.DOWNLOAD_FOLDER, f"{track.name}.%(ext)s"),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',  # Change to 'aac', 'flac', 'wav', 'alac' as needed
                    'preferredquality': '192',  # Bitrate for MP3/AAC
                }],
                'quiet': False
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=True)

                # todo: Check file exist before downloading

                if 'entries' in info:
                    video_info = info['entries'][0]
                else:
                    video_info = info

                file_path = ydl.prepare_filename(video_info)
                file_path = os.path.splitext(file_path)[0] + '.mp3'

                SpotifyDownloadService._embed_track_metadata(file_path, track)

                track.download_location = os.path.join(os.getcwd(), file_path)
                track.notes_errors = f"Successfully Downloaded"
                db.session.add(track)
                db.session.commit()
                logger.info("Downloaded track '%s' to '%s'", track.name, file_path)

        except Exception as e:
            logger.error("Error downloading track '%s': %s", query, e, exc_info=True)
            track.notes_errors = str(e)
            db.session.add(track)
            db.session.commit()

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
        #                     text=f"{track_popularity}")  # todo: Needs fixing after mp3 update

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
    #
    # @staticmethod
    # def _safe_filename(s: str, max_length: int = 255) -> str:
    #     """Sanitize a string making it safe to use as a filename.
    #
    #     This function keeps ASCII and non-ASCII alphanumeric characters,
    #     and removes characters that are not allowed in filenames according
    #     to NTFS and general filesystem conventions.
    #
    #     :param s:A string to make safe for use as a file name.
    #     :param max_length: The maximum filename character length.
    #     :returns: A sanitized string.
    #     """
    #     # Characters in range 0-31 (0x00-0x1F) are not allowed in ntfs filenames.
    #     # Additionally, certain symbols are not allowed in filenames.
    #     # We use a regex pattern that keeps ASCII and non-ASCII alphanumeric characters,
    #     # and replaces other characters.
    #
    #     pattern = r'[^\w\-_\. ]'  # This keeps letters, digits, underscore, hyphen, dot, and space.
    #     regex = re.compile(pattern, re.UNICODE)
    #     filename = regex.sub("", s)
    #
    #     # Truncate to max_length and remove trailing spaces
    #     return filename[:max_length].rstrip()
    #
    # @staticmethod
    # def _remove_diacritics(s: str) -> str:
    #     """
    #     Remove diacritics from a string and replace them with their ASCII equivalents.
    #
    #     :param s: The input string with diacritics.
    #     :return: A string with diacritics replaced by ASCII characters.
    #     """
    #     # Normalize the string to decompose the diacritic characters
    #     normalized = unicodedata.normalize('NFKD', s)
    #
    #     # Filter out non-ASCII characters
    #     return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn' and ord(c) < 128)
    #
    # def _search_video(self, search_query: str) -> Optional[YouTube]:
    #     """
    #     Search YouTube with the given query and return the first video result.
    #
    #     :param search_query: The query string to search on YouTube.
    #     :return: The first YouTube video object found or None if no results.
    #     """
    #     search = Search(search_query)
    #     if search_results := search.results:
    #         self.logger.debug(f"Search results for {search_query}: {search_results[0]}")
    #         return search_results[0]
    #     else:
    #         self.logger.warning(f"No search results for {search_query}")
    #         return None
    #
    # def _search_video_url(self, search_url: str) -> Optional[YouTube]:
    #     """
    #     Search YouTube for the video corresponding to the given URL.
    #
    #     :param search_url: The URL string of the YouTube video.
    #     :return: The YouTube video object if found, otherwise None.
    #     """
    #
    #     def po_token_verifier() -> Tuple[str, str]:
    #         return ("CgtScEJILUJtV0RvcyjR6di8BjIKCgJHQhIEGgAgVg%3D%3D", "MnQ-Fjuq8uj1kD4uz0N69XaWy49X8mgjqSusiExrlDfN9UhOnbehNX1zqkjRbwoJJeOmMhre_WuYxtR4JvaxrjCr3SfEfeTCjFsZUa2CFNUhDiU__dPl2-4xBMZv58JrSaCRAKm4Q5UoAAXjlvl1m9kyaN4vHA==")
    #
    #     try:
    #         video = YouTube(search_url, "Web", allow_oauth_cache=True)
    #         self.logger.debug(f"Found video from URL: {video.title}")
    #         return video
    #     except VideoUnavailable:
    #         self.logger.warning(f"Video unavailable for URL: {search_url}")
    #         return None
    #
    # def _download_audio(self, video: YouTube) -> str:
    #     """
    #     Download the highest quality audio stream of the given YouTube video.
    #
    #     :param video: The YouTube video object from which to download audio.
    #     :return: The file path of the downloaded audio, if available.
    #     """
    #     # Override this function to avoid Streams doing a file size check which will here always be different from raw
    #     # file, I assume due to metadata (image including) on audio files.
    #     def override_exists_at_path(file_path: str) -> bool:
    #         mp3_file_path = os.path.splitext(file_path)[0] + '.mp3'
    #         return os.path.isfile(mp3_file_path)
    #
    #     audio_stream = video.streams.get_audio_only()
    #     if audio_stream:
    #         audio_stream.exists_at_path = override_exists_at_path
    #         file_name = self._remove_diacritics(audio_stream.default_filename)
    #         file_name = self._safe_filename(file_name)
    #         file_path = audio_stream.download(filename=file_name, output_path=self.track_dir)
    #         return self.convert_to_mp3(file_path)
    #     else:
    #         self.logger.warning(f"No audio stream available for this video {video}")
    #
    # @staticmethod
    # def _convert_to_mp3(mp4_file: str) -> str:
    #     """
    #     Convert an MP4 file to MP3 format, delete the original MP4 file, and return the name of the MP3 file.
    #
    #     :param mp4_file: The path to the MP4 file.
    #     :return: The path of the created MP3 file.
    #     """
    #     mp3_file = os.path.splitext(mp4_file)[0] + '.mp3'
    #
    #     if os.path.isfile(mp3_file):
    #         return mp3_file
    #
    #     video_clip = AudioFileClip(mp4_file)
    #     video_clip.write_audiofile(mp3_file)
    #     video_clip.close()
    #
    #     # Delete the original MP4 file
    #     os.remove(mp4_file)
    #
    #     return mp3_file
