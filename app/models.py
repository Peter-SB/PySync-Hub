from datetime import datetime
from app.extensions import db


class Playlist(db.Model):
    __tablename__ = 'playlists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    external_id = db.Column(db.String(255), nullable=False)
    last_synced = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_url = db.Column(db.String(500))  # Store album art URL
    url = db.Column(db.String)
    track_count = db.Column(db.Integer)  # Store the number of tracks on the platform
    #downloaded_track_count = db.Column(db.Integer)  # Store the number of downloaded tracks
    download_status = db.Column(db.String(255))  # "ready", "queued", "downloading"
    disabled = db.Column(db.Boolean, default=False)

    tracks = db.relationship('PlaylistTrack', back_populates='playlist', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'platform': self.platform,
            'external_id': self.external_id,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None,
            'created_at': self.created_at.isoformat(),
            'image_url': self.image_url,
            'track_count': self.track_count,
            'url': self.url,
            #'downloaded_track_count': self.track_count,
            'download_status': self.download_status,
            'disabled': self.disabled
        }


class Track(db.Model):
    __tablename__ = 'tracks'
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.String, nullable=False)
    platform = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    artist = db.Column(db.String, nullable=False)
    download_url = db.Column(db.String, nullable=True)
    download_location = db.Column(db.String, nullable=True)
    album = db.Column(db.String, nullable=True)
    album_art_url = db.Column(db.String, nullable=True)
    notes_errors = db.Column(db.Text)

    __table_args__ = (
    db.UniqueConstraint('platform', 'platform_id', name='uq_platform_track'),)  # Prevent duplicate tracks


class PlaylistTrack(db.Model):
    __tablename__ = 'playlist_tracks'
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id', ondelete="CASCADE"), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('tracks.id', ondelete="CASCADE"), nullable=False)
    track_order = db.Column(db.Integer, nullable=False)

    playlist = db.relationship('Playlist', back_populates='tracks')
    track = db.relationship('Track')

    __table_args__ = (
    db.UniqueConstraint('playlist_id', 'track_id', name='uq_playlist_track'),)  # Avoid duplicate track in a playlist
