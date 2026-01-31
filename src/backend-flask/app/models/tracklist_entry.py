from app.extensions import db


class TracklistEntry(db.Model):
    """Model for individual tracks within a tracklist."""
    __tablename__ = 'tracklist_entries'

    id = db.Column(db.Integer, primary_key=True)
    tracklist_id = db.Column(db.Integer, db.ForeignKey('tracklists.id'), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('tracks.id'))
    track_order = db.Column(db.Integer, nullable=False)
    raw_track_string = db.Column(db.String(500))
    predicted_track_name = db.Column(db.String(255))
    predicted_track_artist = db.Column(db.String(255))
    confidence_score = db.Column(db.Float)
    is_confirmed = db.Column(db.Boolean, default=False)

    # Relationships
    tracklist = db.relationship('Tracklist', back_populates='tracklist_entries')
    track = db.relationship('Track')

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'tracklist_id': self.tracklist_id,
            'track_id': self.track_id,
            'track_order': self.track_order,
            'raw_track_string': self.raw_track_string,
            'predicted_track_name': self.predicted_track_name,
            'predicted_track_artist': self.predicted_track_artist,
            'confidence_score': self.confidence_score,
            'is_confirmed': self.is_confirmed,
            'track': self.track.to_dict() if self.track else None
        }
