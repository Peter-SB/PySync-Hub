from app.extensions import db
from app.models.playlist_track import PlaylistTrack

class Playlist(db.Model):
    __tablename__ = 'playlists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    external_id = db.Column(db.String(255), nullable=False)
    last_synced = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=db.func.utcnow())
    image_url = db.Column(db.String(500))
    url = db.Column(db.String)
    track_count = db.Column(db.Integer)
    download_status = db.Column(db.String(255))
    disabled = db.Column(db.Boolean, default=False)
    download_progress = db.Column(db.Integer, default=0)
    date_limit = db.Column(db.DateTime, nullable=True)
    track_limit = db.Column(db.Integer, nullable=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    custom_order = db.Column(db.Integer, nullable=False, default=0)

    tracks = db.relationship('PlaylistTrack',
                             back_populates='playlist',
                             cascade="all, delete-orphan",
                             order_by="PlaylistTrack.track_order")

    @property
    def downloaded_track_count(self):
        return sum(1 for pt in self.tracks if pt.track and pt.track.download_location)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'platform': self.platform,
            'external_id': self.external_id,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None,
            'created_at': self.created_at.isoformat(),
            'image_url': self.image_url,
            'tracks': [pt.track.to_dict() for pt in self.tracks if pt.track],
            'track_count': self.track_count,
            'url': self.url,
            'downloaded_track_count': self.downloaded_track_count,
            'download_status': self.download_status,
            'disabled': self.disabled,
            'download_progress': 0,
            'date_limit': self.date_limit.isoformat() if self.date_limit else None,
            'track_limit': self.track_limit,
            'folder_id': self.folder_id,
            'custom_order': self.custom_order,
        }
