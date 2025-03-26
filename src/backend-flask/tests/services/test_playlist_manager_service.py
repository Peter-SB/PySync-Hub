import pytest

from app.models import Playlist
from app.extensions import db
from app.services.playlist_manager_service import PlaylistManagerService


@pytest.mark.usefixtures("client", "init_database")
class TestSyncPlaylists():
    """Tests for the sync_playlists function in PlaylistManagerService."""

    def test_sync_playlist_updates_info_spotify(self, app):
        fake_playlist = Playlist(
            id=1,
            name="Old Playlist",
            platform="spotify",
            external_id="3bL14BgPXekKHep3RRdwGZ",
            image_url="http://oldimage.com/image.png",
            track_count=0,
            url="https://open.spotify.com/playlist/3bL14BgPXekKHep3RRdwGZ",
            download_status="ready"
        )
        with app.app_context():
            db.session.add(fake_playlist)
            db.session.commit()

            playlist_response = PlaylistManagerService.sync_playlists([fake_playlist])
            assert playlist_response[0].name == "Test Playlist 1"

            updated_playlist = Playlist.query.filter_by(external_id="3bL14BgPXekKHep3RRdwGZ").first()
            assert updated_playlist.name == "Test Playlist 1"
            assert updated_playlist.track_count == 2

    def test_sync_playlist_updates_info_soundcloud(self, app):
        fake_playlist = Playlist(
            id=1,
            name="Old Playlist",
            platform="soundcloud",
            external_id="1890498842",
            image_url="http://oldimage.com/image.png",
            track_count=0,
            url="https://soundcloud.com/schmoot-point/sets/omwhp",
            download_status="ready"
        )
        with app.app_context():
            db.session.add(fake_playlist)
            db.session.commit()

            playlist_response = PlaylistManagerService.sync_playlists([fake_playlist])
            assert playlist_response[0].name == "OMWHP"

            updated_playlist = Playlist.query.filter_by(external_id="1890498842").first()
            assert updated_playlist.name == "OMWHP"
            assert updated_playlist.track_count == 14

