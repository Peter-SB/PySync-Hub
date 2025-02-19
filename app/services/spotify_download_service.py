import os
import logging
import threading

from config import Config
from app.models import Playlist, Track
from pytubefix import YouTube, Search
from app.extensions import db

logger = logging.getLogger(__name__)

class SpotifyDownloadService:
    @staticmethod
    def download_tracks_for_playlist(playlist_id: int) -> None:
        """
        For a given playlist (by its internal ID), iterate over its tracks.
        For each track, search YouTube using the track name and artist, then
        download the best available audio stream to the download folder.
        Finally, update the track record with the YouTube URL (used to download)
        and the local download path.
        """
        # Retrieve the playlist from the database
        playlist = db.session.get(Playlist, playlist_id)
        if not playlist:
            logger.error("Playlist with id %s not found.", playlist_id)
            return

        # Iterate over each track in the playlist (via the PlaylistTrack relationship)
        # If the track is already downloaded, skip it.
        tracks = [pt.track for pt in playlist.tracks]
        for track in tracks:
            if track.download_location:
                logger.info("Track '%s' already downloaded, skipping.", track.name)
                continue

            # Build a search query combining the track name and artist
            query = f"{track.name} {track.artist}"
            logger.info("Searching YouTube for track: '%s'", query)
            try:
                # Perform a YouTube search using pytube's Search class
                search = Search(query)
                if not search.results:
                    error_msg = f"No YouTube results found for track: '{query}'"
                    logger.error(error_msg)
                    track.notes_errors = error_msg
                    db.session.add(track)
                    db.session.commit()
                    continue

                # Pick the first result
                video = search.results[0]
                video_url = video.watch_url
                track.download_url = video_url
                logger.info("Found YouTube video URL '%s' for track: '%s'", video_url, query)

                # Create a YouTube object to access streams
                yt = YouTube(video_url, "WEB")
                # Choose an audio-only stream – ordering by bitrate (highest first)
                audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
                if not audio_stream:
                    error_msg = f"No audio stream available for video: '{video_url}'"
                    logger.error(error_msg)
                    track.notes_errors = error_msg
                    db.session.add(track)
                    db.session.commit()
                    continue

                # Download the audio stream to the specified download folder
                logger.info("Downloading track '%s'...", track.name)
                file_path = audio_stream.download(output_path=Config.DOWNLOAD_FOLDER)
                logger.info("Downloaded '%s' to '%s'", track.name, file_path)

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
    def download_playlist(playlist: Playlist, cancellation_flags: dict[threading.Event]):
        # Ensure a cancellation flag exists for this playlist.
        if playlist.id not in cancellation_flags:
            cancellation_flags[playlist.id] = threading.Event()

        # Update the playlist status to 'downloading'
        playlist.download_status = 'downloading'
        db.session.commit()

        # Iterate over the tracks and download each one.
        tracks = [pt.track for pt in playlist.tracks]
        for track in tracks:
            # Check if cancellation has been requested.
            if cancellation_flags[playlist.id].is_set():
                print(f"Download for playlist {playlist.name} cancelled. (id: {playlist.id})")
                playlist.download_status = 'ready'
                db.session.commit()
                break

            try:
                SpotifyDownloadService.download_track(track)
            except Exception as e:
                print(f"Error downloading track {track.name}: {e}")

        # After finishing (or if cancelled) update status back to 'ready'
        logger.info("Download Finished for Playlist '%s'", playlist.name)
        playlist.download_status = 'ready'
        db.session.commit()
        # Clear the cancellation flag for future downloads.
        cancellation_flags[playlist.id].clear()

    @staticmethod
    def download_track(track: Track):
        if track.download_location and os.path.isfile(track.download_location):
            logger.info("Track '%s' already downloaded, skipping.", track.name)
            return

        # Build a search query combining the track name and artist
        query = f"{track.name} {track.artist}"
        logger.info("Searching YouTube for track: '%s'", query)
        try:
            # Perform a YouTube search using pytube's Search class
            search = Search(query)
            if not search.results:
                error_msg = f"No YouTube results found for track: '{query}'"
                logger.error(error_msg)
                track.notes_errors = error_msg
                db.session.add(track)
                db.session.commit()
                return

            # Pick the first result
            video = search.results[0]
            video_url = video.watch_url
            track.download_url = video_url
            logger.info("Found YouTube video URL '%s' for track: '%s'", video_url, query)

            # Create a YouTube object to access streams
            yt = YouTube(video_url, "WEB")
            # Choose an audio-only stream – ordering by bitrate (highest first)
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if not audio_stream:
                error_msg = f"No audio stream available for video: '{video_url}'"
                logger.error(error_msg)
                track.notes_errors = error_msg
                db.session.add(track)
                db.session.commit()
                return

            # Download the audio stream to the specified download folder
            logger.info("Downloading track '%s'...", track.name)
            file_path = audio_stream.download(output_path=Config.DOWNLOAD_FOLDER)
            logger.info("Downloaded '%s' to '%s'", track.name, file_path)

            # Update the track record with the downloaded file location
            track.download_location = file_path
            db.session.add(track)
            db.session.commit()

        except Exception as e:
            logger.error("Error downloading track '%s': %s", query, e, exc_info=True)
            track.notes_errors = str(e)
            db.session.add(track)
            db.session.commit()