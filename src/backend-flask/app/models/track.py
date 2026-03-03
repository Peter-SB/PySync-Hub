from app.extensions import db
from app.utils.file_download_utils import FileDownloadUtils

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
        db.UniqueConstraint('platform', 'platform_id', name='uq_platform_track'),)

    @property
    def absolute_download_path(self):
        if not self.download_location:
            return None
        return FileDownloadUtils.get_absolute_path(self.download_location)

    def set_download_location(self, absolute_path):
        if absolute_path:
            self.download_location = FileDownloadUtils.get_relative_path(absolute_path)
        else:
            self.download_location = None

    def is_downloaded(self):
        return FileDownloadUtils.is_track_already_downloaded(self.download_location)

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
            'download_location': self.absolute_download_path,
            'notes_errors': self.notes_errors,
        }
