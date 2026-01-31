from typing import Optional
from app.extensions import db


class TracklistEntry(db.Model):
    __tablename__ = 'tracklist_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    tracklist_id = db.Column(db.Integer, db.ForeignKey('tracklists.id'), nullable=False)
    
    full_tracklist_entry = db.Column(db.Text, nullable=False)  # Original full tracklist entry for reference
    
    artist = db.Column(db.String(500), nullable=True)  # Cleaned artist names
    short_title = db.Column(db.String(500), nullable=True)  # Title without version info
    full_title = db.Column(db.String(500), nullable=True)  # Full title including version info
    version = db.Column(db.String(500), nullable=True)  # Remix/edit/bootleg title
    
    version_artist = db.Column(db.String(500), nullable=True)  # For matching just the artist string from version info
    is_vip = db.Column(db.Boolean, default=False)  # Is it a VIP version, this is a strong signal
    
    unicode_cleaned_entry = db.Column(db.Text, nullable=True)  # Unicode cleaned version of the entry
    prefix_cleaned_entry = db.Column(db.Text, nullable=True)  # Prefix cleaned version of the entry
    is_unidentified = db.Column(db.Boolean, default=False)  # Whether the track is identified or marked as "ID"
    
    predicted_track_id = db.Column(db.Integer, db.ForeignKey('tracks.id'), nullable=True)  # Best predicted match
    confirmed_track_id = db.Column(db.Integer, db.ForeignKey('tracks.id'), nullable=True)  # User-confirmed match
    
    favourite = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, nullable=True)

    # Relationships
    tracklist = db.relationship('Tracklist', back_populates='tracklist_entries')
    predicted_track = db.relationship('Track', foreign_keys=[predicted_track_id])
    confirmed_track = db.relationship('Track', foreign_keys=[confirmed_track_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'tracklist_id': self.tracklist_id,
            'full_tracklist_entry': self.full_tracklist_entry,
            'artist': self.artist,
            'short_title': self.short_title,
            'full_title': self.full_title,
            'version': self.version,
            'version_artist': self.version_artist,
            'is_vip': self.is_vip,
            'unicode_cleaned_entry': self.unicode_cleaned_entry,
            'prefix_cleaned_entry': self.prefix_cleaned_entry,
            'is_unidentified': self.is_unidentified,
            'predicted_track_id': self.predicted_track_id,
            'confirmed_track_id': self.confirmed_track_id,
            'favourite': self.favourite,
            'order_index': self.order_index,
            'predicted_track': self.predicted_track.to_dict() if self.predicted_track else None,
            'confirmed_track': self.confirmed_track.to_dict() if self.confirmed_track else None
        }