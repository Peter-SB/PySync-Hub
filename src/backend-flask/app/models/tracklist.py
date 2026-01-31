from datetime import datetime
from app.extensions import db


class Tracklist(db.Model):
    """Model for storing tracklists/setlists."""
    __tablename__ = 'tracklists'

    id = db.Column(db.Integer, primary_key=True)
    set_name = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255))
    tracklist_string = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)
    image_url = db.Column(db.String(500))
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tracklist_entries = db.relationship('TracklistEntry', back_populates='tracklist', cascade='all, delete-orphan')
    folder = db.relationship('Folder', back_populates='tracklists')

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'set_name': self.set_name,
            'artist': self.artist,
            'tracklist_string': self.tracklist_string,
            'rating': self.rating,
            'image_url': self.image_url,
            'folder_id': self.folder_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tracklist_entries': [entry.to_dict() for entry in self.tracklist_entries] if self.tracklist_entries else []
        }
