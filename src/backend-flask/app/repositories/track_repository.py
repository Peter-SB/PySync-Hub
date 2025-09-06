import logging
from datetime import datetime
from typing import List, Optional

from app.extensions import db, socketio
from app.models import Playlist, PlaylistTrack, Track
from app.utils.db_utils import commit_with_retries

logger = logging.getLogger(__name__)


class TrackRepository:
    @staticmethod
    def remove_tracks_before_date(playlist, date_limit) -> List[Track]:
        if date_limit:
            pts_to_remove = [
                pt for pt in playlist.tracks
                if pt.added_on and pt.added_on.date() < date_limit
            ]
            for pt in pts_to_remove:
                playlist.tracks.remove(pt)
            commit_with_retries(db.session)
        return [pt.track for pt in playlist.tracks]

    @staticmethod
    def remove_excess_tracks(playlist, new_track_limit) -> List[Track]:
        if new_track_limit < len(playlist.tracks):
            excess_pts = playlist.tracks[new_track_limit:]
            for pt in excess_pts:
                playlist.tracks.remove(pt)
        return [pt.track for pt in playlist.tracks]

    @staticmethod
    def get_track_added_on(playlist: 'Playlist', playlist_track: 'PlaylistTrack') -> Optional[datetime]:
        return playlist_track.added_on.date() if playlist_track and playlist_track.added_on else None

    @staticmethod
    def get_track_index(playlist: 'Playlist', track: 'Track') -> Optional[int]:
        for index, playlist_track in enumerate(playlist.tracks):
            if playlist_track.track_id == track.id:
                return index
        return None