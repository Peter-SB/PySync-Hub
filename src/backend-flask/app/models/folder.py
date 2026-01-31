from app.extensions import db

class Folder(db.Model):
    __tablename__ = 'folders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    custom_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=db.func.utcnow())
    disabled = db.Column(db.Boolean, default=True)
    expanded = db.Column(db.Boolean, default=True)

    subfolders = db.relationship(
        'Folder',
        backref=db.backref('parent', remote_side=[id]),
        cascade="all, delete-orphan"
    )

    playlists = db.relationship(
        'Playlist',
        backref='folder',
        cascade="all"
    )

    tracklists = db.relationship(
        'Tracklist',
        back_populates='folder',
        cascade="all"
    )

    def children_count(self):
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
