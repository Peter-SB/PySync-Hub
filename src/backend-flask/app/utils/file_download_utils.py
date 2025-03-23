import logging
import os
import re

import requests
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1
from mutagen.mp3 import MP3

from app.models import Track

logger = logging.getLogger(__name__)

class FileDownloadUtils:
    @staticmethod
    def is_track_already_downloaded(track: Track) -> bool:
        """Check if the track is already downloaded and update the database accordingly."""
        if track.download_location and os.path.isfile(track.download_location):
            logger.info("Track '%s' already downloaded, skipping.", track.name)
            #track.notes_errors = "Already Downloaded, Skipped"
            #db.session.add(track)
            #db.session.commit()
            return True
        return False

    @staticmethod
    def embed_track_metadata(file_path, track: Track):
        """
        Adds metadata from the track data to the MP3 audio file, including cover art if available.

        :param track: Track data from Spotify.
        :param track_file_path: Path to the MP3 audio file.
        """
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