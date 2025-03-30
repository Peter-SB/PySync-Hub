import logging
from datetime import datetime
from typing import List

from app.extensions import db, socketio
from app.models import Playlist, PlaylistTrack, Track

logger = logging.getLogger(__name__)


class TrackRepository:
    @staticmethod
    def remove_excess_tracks(playlist, new_track_limit) -> List[Track]:
        if new_track_limit < len(playlist.tracks):
            # Remove excess tracks
            excess_tracks = playlist.tracks[new_track_limit:]
            for pt in excess_tracks:
                db.session.delete(pt)
            db.session.commit()
        return [pt.track for pt in playlist.tracks]

    @staticmethod
    def remove_tracks_before_date(playlist, date_limit) -> List[Track]:
        if date_limit:
            tracks_to_remove = [pt for pt in playlist.tracks if pt.track and pt.track.created_at < date_limit]
            for pt in tracks_to_remove:
                db.session.delete(pt)
            db.session.commit()
        return [pt.track for pt in playlist.tracks]

    @staticmethod
    def get_track_added_date(playlist: Playlist, track: Track) -> datetime:
        for pt in playlist.tracks:
            if pt.track.id == track.id:
                return pt.track.created_at
