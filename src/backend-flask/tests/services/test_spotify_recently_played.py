import pytest

from app.models import Playlist, Track
from app.extensions import db
from app.services.platform_services.spotify_service import SpotifyService
from app.services.playlist_manager_service import PlaylistManagerService


@pytest.mark.usefixtures("client", "init_database")
class TestSpotifyRecentlyPlayed:
    """Tests for Spotify Recently Played functionality."""

    def test_get_recently_played_playlist_data(self, app):
        """Test getting recently played playlist metadata."""
        with app.app_context():
            playlist_data = SpotifyService.get_playlist_data("https://open.spotify.com/recently-played")
            
            assert playlist_data is not None
            assert playlist_data['name'] == "Your Recently Played Spotify Songs"
            assert playlist_data['external_id'] == "recently-played"
            assert playlist_data['platform'] == "spotify"
            assert playlist_data['url'] == "https://open.spotify.com/recently-played"
            assert 'track_count' in playlist_data

    def test_get_recently_played_tracks_filters_downloaded_only(self, app):
        """
        Test that recently played tracks are filtered to only include tracks
        that are already downloaded in the database.
        """
        with app.app_context():
            # Add some tracks to the database
            # track1 is downloaded (has download_location)
            track1 = Track(
                platform_id="track1",
                platform="spotify",
                name="Recently Played Song 1",
                artist="Artist One",
                album="Album One",
                download_location="music/track1.mp3"
            )
            db.session.add(track1)
            
            # track2 is NOT downloaded (no download_location)
            track2 = Track(
                platform_id="track2",
                platform="spotify",
                name="Recently Played Song 2",
                artist="Artist Two",
                album="Album Two",
                download_location=None
            )
            db.session.add(track2)
            
            # track3 doesn't exist in database at all
            
            db.session.commit()
            
            # Get recently played tracks
            tracks = SpotifyService._get_recently_played_tracks()
            
            # Should only return track1 (the one that's downloaded)
            assert len(tracks) == 1
            assert tracks[0]['platform_id'] == "track1"
            assert tracks[0]['name'] == "Recently Played Song 1"

    def test_get_recently_played_tracks_empty_when_no_downloaded(self, app):
        """Test that recently played returns empty list when no tracks are downloaded."""
        with app.app_context():
            # Add tracks to database but none are downloaded
            track1 = Track(
                platform_id="track1",
                platform="spotify",
                name="Recently Played Song 1",
                artist="Artist One",
                download_location=None
            )
            db.session.add(track1)
            db.session.commit()
            
            # Get recently played tracks
            tracks = SpotifyService._get_recently_played_tracks()
            
            # Should return empty list
            assert len(tracks) == 0

    def test_get_recently_played_tracks_empty_database(self, app):
        """Test that recently played handles empty database gracefully."""
        with app.app_context():
            # No tracks in database at all
            tracks = SpotifyService._get_recently_played_tracks()
            
            # Should return empty list
            assert len(tracks) == 0

    def test_add_recently_played_playlist(self, app):
        """Test adding recently played playlist through PlaylistManagerService."""
        with app.app_context():
            # Add a downloaded track so the playlist has something
            track1 = Track(
                platform_id="track1",
                platform="spotify",
                name="Recently Played Song 1",
                artist="Artist One",
                album="Album One",
                download_location="music/track1.mp3"
            )
            db.session.add(track1)
            db.session.commit()
            
            # Add the recently played playlist
            error = PlaylistManagerService.add_playlists("https://open.spotify.com/recently-played")
            
            # Should succeed
            assert error is None
            
            # Verify playlist was created
            playlist = Playlist.query.filter_by(
                external_id="recently-played",
                platform="spotify"
            ).first()
            
            assert playlist is not None
            assert playlist.name == "Your Recently Played Spotify Songs"
            
            # Verify only downloaded tracks are in the playlist
            assert len(playlist.tracks) == 1
            assert playlist.tracks[0].track.platform_id == "track1"

    def test_recently_played_playlist_sync(self, app):
        """Test syncing recently played playlist updates tracks correctly."""
        with app.app_context():
            # Create the recently played playlist
            playlist = Playlist(
                name="Old Name",
                platform="spotify",
                external_id="recently-played",
                url="https://open.spotify.com/recently-played"
            )
            db.session.add(playlist)
            db.session.commit()
            
            # Add a downloaded track
            track1 = Track(
                platform_id="track1",
                platform="spotify",
                name="Recently Played Song 1",
                artist="Artist One",
                album="Album One",
                download_location="music/track1.mp3"
            )
            db.session.add(track1)
            db.session.commit()
            
            # Sync the playlist
            PlaylistManagerService.sync_playlists([playlist])
            
            # Verify playlist was updated
            updated_playlist = Playlist.query.filter_by(external_id="recently-played").first()
            assert updated_playlist.name == "Your Recently Played Spotify Songs"
            assert updated_playlist.last_synced is not None
