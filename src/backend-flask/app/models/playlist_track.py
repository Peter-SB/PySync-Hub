from app.extensions import db

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
        db.UniqueConstraint('playlist_id', 'track_id', name='uq_playlist_track'),)
