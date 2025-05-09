import logging
import os
import re

import requests
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1
from mutagen.mp3 import MP3

from config import Config

logger = logging.getLogger(__name__)

class FileDownloadUtils:
    @staticmethod
    def is_track_already_downloaded(download_location) -> bool:
        """Check if the track is already downloaded and update the database accordingly."""

        absolute_path = FileDownloadUtils.get_absolute_path(download_location)
        if download_location and os.path.isfile(absolute_path):
            return True
        return False

    @staticmethod
    def embed_track_metadata(file_path, track):
        """
        Adds metadata from the track data to the MP3 audio file, including cover art if available.

        :param track: Track data object with name, artist, album, etc.
        :param file_path: Path to the MP3 audio file.
        """
        logger.info(f"Embedding metadata for track '{track.name}' at '{file_path}'")

        audio = MP3(file_path, ID3=ID3)

        track_name = track.name
        track_artist = track.artist
        # track_artists = ", ".join([artist["name"] for artist in track_data["artists"]])
        # track_popularity = track_data["popularity"]
        track_album = track.album
        track_cover_imgs = track.album_art_url

        # Basic metadata
        audio['TIT2'] = TIT2(encoding=3, text=track_name)
        audio['TPE1'] = TPE1(encoding=3, text=track_artist)
        if track_album:  # soundcloud doesn't have album info
            audio['TALB'] = TALB(encoding=3, text=track_album)

        # audio['COMM'] = COMM(encoding=3, lang='eng', desc=f'Popularity = {track_popularity}',
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

    @staticmethod
    def sanitize_filename(s: str, max_length: int = 255) -> str:
        """Sanitize a string making it safe to use as a filename."""
        pattern = r'[^\w\-_\. ]'  # This keeps letters, digits, underscore, hyphen, dot, and space.
        regex = re.compile(pattern, re.UNICODE)
        filename = regex.sub("", s)

        # Truncate to max_length and remove trailing spaces
        return filename[:max_length].rstrip()
    
    @staticmethod
    def get_relative_path(absolute_path):
        """Convert an absolute file path to a path relative to the DOWNLOAD_FOLDER.
        
        Returns None if the path is not in the download folder.
        """
        if not absolute_path:
            return None
            
        if not os.path.isabs(absolute_path):
            # Already a relative path
            return absolute_path
            
        download_folder = Config.DOWNLOAD_FOLDER
        try:
            # Make both paths absolute and normalized
            abs_path = os.path.abspath(absolute_path)
            abs_download = os.path.abspath(download_folder)
            
            if abs_path.startswith(abs_download):
                # Get the part of the path after the download folder
                rel_path = os.path.relpath(abs_path, abs_download)
                return rel_path
            else:
                logger.warning(f"Path {absolute_path} is not within the download folder {download_folder}")
                return absolute_path  # Return as is if not in download folder
        except Exception as e:
            logger.error(f"Error converting to relative path: {e}")
            return absolute_path
            
    @staticmethod
    def get_absolute_path(relative_path):
        """Convert a path relative to DOWNLOAD_FOLDER to an absolute path.
        
        If the path is already absolute, returns it unchanged.
        """
        if not relative_path:
            return None
            
        if os.path.isabs(relative_path):
            # Already an absolute path
            return relative_path
            
        # Join with the download folder to get the absolute path
        return os.path.join(Config.DOWNLOAD_FOLDER, relative_path)