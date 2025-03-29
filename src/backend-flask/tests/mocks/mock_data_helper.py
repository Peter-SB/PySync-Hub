import json
import os
import logging
from datetime import datetime

from app.extensions import db
from app.models import Playlist, Track, PlaylistTrack  # adjust the import path as needed

logger = logging.getLogger(__name__)

MOCK_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../mock_data")

class MockPlaylistDataHelper:
    @staticmethod
    def save_data(playlist):
        """
        Save the playlist, its associated tracks, and their order to a JSON file.
        The JSON file is named: "mock_playlist_data_{playlist.name}.json".
        """
        data = {}
        data["playlist"] = playlist.to_dict()
        tracks = []
        playlist_tracks = []
        seen_track_ids = set()
        for pt in playlist.tracks:
            track = pt.track
            # Avoid duplicating track records if the same track appears more than once.
            if track.id not in seen_track_ids:
                tracks.append(track.to_dict())
                seen_track_ids.add(track.id)
            # Record the order of the track within the playlist.
            playlist_tracks.append({
                "track_id": track.id,
                "track_order": pt.track_order
            })

        data["tracks"] = tracks
        data["playlist_tracks"] = playlist_tracks

        # Create filename using the playlist name.
        filename = os.path.join(MOCK_DATA_DIR, f"mock_playlist_data_{playlist.name}.json")
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        logger.info(f"Saved playlist data to {filename}")

    @staticmethod
    def load_data(playlist_name):
        """
        Load the JSON file "mock_playlist_data_{playlist_name}.json" and insert the data
        into the database. This function creates a new playlist record, the related tracks,
        and sets up the playlist_tracks relationship preserving the order.
        """
        filename = os.path.join(MOCK_DATA_DIR, f"mock_playlist_data_{playlist_name}.json")
        if not os.path.exists(filename):
            logger.error(f"File {filename} does not exist.")
            return

        with open(filename, "r", encoding="UTF-8") as f:
            data = json.load(f)

        logger.info(f"Loading playlist data from {filename} into the database. playlist_data: {data.get('playlist')}")

        # ----------------------------
        # Load Playlist Data
        # ----------------------------
        playlist_data = data["playlist"]
        # Remove computed properties not needed for instantiation.
        playlist_data.pop("downloaded_track_count", None)
        # Convert ISO date strings back to datetime objects.
        if playlist_data.get("last_synced"):
            playlist_data["last_synced"] = datetime.fromisoformat(playlist_data["last_synced"])
        if playlist_data.get("created_at"):
            playlist_data["created_at"] = datetime.fromisoformat(playlist_data["created_at"])
        # Extract and remove the id from the dict to set it manually.
        playlist_id = playlist_data.pop("id", None)
        playlist = Playlist(**playlist_data)
        if playlist_id is not None:
            playlist.id = playlist_id
        db.session.add(playlist)
        db.session.commit()  # commit so the playlist is available

        # ----------------------------
        # Load Tracks Data
        # ----------------------------
        tracks_map = {}
        for track_data in data["tracks"]:
            # Remove id from kwargs and set it manually.
            saved_track_id = track_data.pop("id", None)
            track = Track(**track_data)
            if saved_track_id is not None:
                track.id = saved_track_id
            db.session.add(track)
            # Build a mapping from saved id to the newly created track
            tracks_map[saved_track_id] = track
        db.session.commit()

        # ----------------------------
        # Load PlaylistTracks Data
        # ----------------------------
        for pt_data in data["playlist_tracks"]:
            saved_track_id = pt_data["track_id"]
            # Use the saved playlist id and the new track id from our mapping.
            playlist_track = PlaylistTrack(
                playlist_id=playlist.id,
                track_id=tracks_map[saved_track_id].id,
                track_order=pt_data["track_order"]
            )
            db.session.add(playlist_track)
        db.session.commit()

        print(f"Playlist data loaded from {filename} into the database.")

        # playlist_data = data.get("playlist")
        # tracks_data = data.get("tracks", [])
        # playlist_tracks_data = data.get("playlist_tracks", [])
        #
        # # Create the playlist record. If the data includes an "id" and you wish to preserve it,
        # # ensure that your testing DB setup allows explicit primary key insertion.
        # playlist = Playlist(**playlist_data)
        # db.session.add(playlist)
        # db.session.flush()  # flush to get an id assigned if not provided
        #
        # # Build a mapping from the old track IDs (from the JSON) to the new track IDs
        # track_id_mapping = {}
        # for track_dict in tracks_data:
        #     track = Track(**track_dict)
        #     db.session.add(track)
        #     db.session.flush()  # assign new track id
        #     # Map the original saved id to the new id
        #     track_id_mapping[track_dict["id"]] = track.id
        #
        # # Create the PlaylistTrack entries using the new track IDs.
        # for pt in playlist_tracks_data:
        #     old_track_id = pt["track_id"]
        #     new_track_id = track_id_mapping.get(old_track_id)
        #     if new_track_id is None:
        #         logger.error(f"Track id {old_track_id} not found in track mapping.")
        #         continue
        #
        #     playlist_track = PlaylistTrack(
        #         playlist_id=playlist.id,
        #         track_id=new_track_id,
        #         track_order=pt["track_order"]
        #     )
        #     db.session.add(playlist_track)
        #
        # db.session.commit()
        # logger.info(f"Loaded playlist data from {filename} into the database.")
