from datetime import datetime
from app import db

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    service = db.Column(db.String(50), nullable=False)
    external_id = db.Column(db.String(255), nullable=False)
    last_synced = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_url = db.Column(db.String(500))  # Store album art URL
    track_count = db.Column(db.Integer)  # Store the number of tracks

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'service': self.service,
            'external_id': self.external_id,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None,
            'created_at': self.created_at.isoformat(),
            'image_url': self.image_url,
            'track_count': self.track_count
        }
