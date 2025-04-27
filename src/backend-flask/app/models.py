import logging
import os
from datetime import datetime

from app.extensions import db

logger = logging.getLogger(__name__)

class Folder(db.Model):
    __tablename__ = 'folders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    custom_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default=True)
    expanded = db.Column(db.Boolean, default=True)

    # Relationship to allow nesting folders (subfolders)
    subfolders = db.relationship(
        'Folder',
        backref=db.backref('parent', remote_side=[id]),
        cascade="all, delete-orphan"
    )

    # Relationship: playlists assigned directly to this folder
    playlists = db.relationship(
        'Playlist',
        backref='folder',
        cascade="all"
    )

    def children_count(self):
        """Returns the number of subfolders and playlists in this folder."""
        return len(self.subfolders) + len(self.playlists)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'custom_order': self.custom_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'disabled': self.disabled,
            'expanded': self.expanded,
            'subfolders': [subfolder.to_dict() for subfolder in self.subfolders],
            'playlists': [playlist.to_dict() for playlist in self.playlists],
            'children_count': self.children_count(),
        }

    def __repr__(self):
        return f'<Folder {self.name}>'

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
    download_status = db.Column(db.String(255))  # "ready", "queued", "downloading"
    disabled = db.Column(db.Boolean, default=False)
    download_progress = db.Column(db.Integer, default=0)
    date_limit = db.Column(db.DateTime, nullable=True)  # Only sync/download tracks added after this date
    track_limit = db.Column(db.Integer, nullable=True)  # Maximum number of tracks to sync/download
    
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    custom_order = db.Column(db.Integer, nullable=False, default=0)

    tracks = db.relationship('PlaylistTrack',
                             back_populates='playlist',
                             cascade="all, delete-orphan",
                             order_by="PlaylistTrack.track_order")

    @property
    def downloaded_track_count(self):
        """Returns the number of tracks in the playlist that have a download location."""
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
            'download_progress': self.download_progress,
            'date_limit': self.date_limit.isoformat() if self.date_limit else None,
            'track_limit': self.track_limit,
            'folder_id': self.folder_id,
            'custom_order': self.custom_order,
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

    def to_dict(self):
        return {
            'id': self.id,
            'platform_id': self.platform_id,
            'platform': self.platform,
            'name': self.name,
            'artist': self.artist,
            'album': self.album,
            'album_art_url': self.album_art_url,
            'download_url': self.download_url,
            'download_location': self.download_location,
            'notes_errors': self.notes_errors,
        }


class PlaylistTrack(db.Model):
    __tablename__ = 'playlist_tracks'
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id', ondelete="CASCADE"), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('tracks.id', ondelete="CASCADE"), nullable=False)
    track_order = db.Column(db.Integer, nullable=False)
    added_on = db.Column(db.DateTime, nullable=True)

    playlist = db.relationship('Playlist', back_populates='tracks')
    track = db.relationship('Track')

    __table_args__ = (
        db.UniqueConstraint('playlist_id', 'track_id',
                            name='uq_playlist_track'),)  # Avoid duplicate track in a playlist
