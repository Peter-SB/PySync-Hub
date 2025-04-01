import logging
from datetime import datetime
from typing import List, Optional

from app.extensions import db, socketio
from app.models import Playlist, PlaylistTrack, Track

logger = logging.getLogger(__name__)


class TrackRepository:
    @staticmethod
    def remove_tracks_before_date(playlist, date_limit) -> List[Track]:
        if date_limit:
            tracks_to_remove = []
            for track in playlist.tracks:
                if TrackRepository.get_track_added_on(playlist, track) < date_limit:
                    tracks_to_remove.append(track)
            for track in tracks_to_remove:
                db.session.delete(track)
            db.session.commit()
        return [pt.track for pt in playlist.tracks]

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
    def get_track_added_on(playlist: Playlist, track: Track) -> datetime:
        playlist_track = PlaylistTrack.query.filter_by(playlist_id=playlist.id, track_id=track.id).first()
        return playlist_track.added_on.date() if playlist_track else None

    @staticmethod
    def get_track_index(playlist: Playlist, track: Track) -> Optional[int]:
        for index, playlist_track in enumerate(playlist.tracks):
            if playlist_track.track_id == track.id:
                return index
        return None