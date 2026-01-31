from typing import Optional
from app.extensions import db


class Tracklist(db.Model):
    __tablename__ = 'tracklists'
    
    id = db.Column(db.Integer, primary_key=True)
    set_name = db.Column(db.String(500), nullable=False)
    artist = db.Column(db.String(500), nullable=True)
    tracklist_string = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    disabled = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(500), nullable=True)
    custom_order = db.Column(db.Integer, nullable=False, default=0)
    download_progress = db.Column(db.Integer, default=0)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    
    # Relationship to tracklist entries
    tracklist_entries = db.relationship('TracklistEntry', back_populates='tracklist', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'set_name': self.set_name,
            'artist': self.artist,
            'tracklist_string': self.tracklist_string,
            'rating': self.rating,
            'disabled': self.disabled,
            'image_url': self.image_url,
            'custom_order': self.custom_order,
            'download_progress': self.download_progress,
            'folder_id': self.folder_id,
            'tracklist_entries': [entry.to_dict() for entry in self.tracklist_entries] if self.tracklist_entries else []
        }

