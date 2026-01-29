"""
Tests for adding playlists when some tracks are already in the database.
Tests each platform service to ensure tracks are reused correctly and not duplicated.
"""
import pytest
from datetime import datetime

from app.models import Playlist, Track, PlaylistTrack
from app.extensions import db
from app.services.playlist_manager_service import PlaylistManagerService


@pytest.mark.usefixtures("client", "init_database")
class TestAddPlaylistWithExistingTracks:
    """Tests for adding playlists when tracks already exist in the database."""

    def test_add_spotify_playlist_with_existing_tracks(self, app):
        """Test adding a Spotify playlist when some tracks already exist in DB."""
        with app.app_context():
            # Add some sample tracks to the database first
            existing_track1 = Track(
                platform_id="track1",
                platform="spotify",
                name="Song One",
                artist="Artist One",
                album="Album One",
                album_art_url="http://example.com/album1.png",
                download_url=None
            )
            existing_track2 = Track(
                platform_id="track2",
                platform="spotify",
                name="Song Two",
                artist="Artist Two",
                album="Album Two",
                album_art_url="http://example.com/album2.png",
                download_url=None
            )
            db.session.add(existing_track1)
            db.session.add(existing_track2)
            db.session.commit()

            # Verify tracks are in DB
            initial_track_count = Track.query.count()
            assert initial_track_count == 2

            # Add a new playlist that contains these tracks
            # The mock data returns track1 and track2
            error = PlaylistManagerService.add_playlists(
                "https://open.spotify.com/playlist/3bL14BgPXekKHep3RRdwGZ"
            )
            
            assert error is None

            # Verify that no duplicate tracks were created
            final_track_count = Track.query.count()
            assert final_track_count == 2, "No new tracks should be created when they already exist"

            # Verify the playlist was created
            playlist = Playlist.query.first()
            assert playlist is not None
            assert playlist.platform == "spotify"
            assert playlist.name == "Test Playlist 1"

            # Verify playlist-track associations were created
            playlist_track_count = PlaylistTrack.query.filter_by(playlist_id=playlist.id).count()
            assert playlist_track_count == 2, "Both tracks should be associated with the playlist"

            # Verify the tracks in the playlist are the existing tracks
            playlist_tracks = PlaylistTrack.query.filter_by(playlist_id=playlist.id).all()
            track_ids = {pt.track_id for pt in playlist_tracks}
            assert existing_track1.id in track_ids
            assert existing_track2.id in track_ids

    def test_add_youtube_playlist_with_existing_tracks(self, app):
        """Test adding a YouTube playlist when some tracks already exist in DB."""
        with app.app_context():
            # Add some sample YouTube tracks to the database first
            # Using track IDs from the mock YouTube service
            existing_track1 = Track(
                platform_id="dQw4w9WgXcQ",
                platform="youtube",
                name="Never Gonna Give You Up",
                artist="Rick Astley",
                album=None,
                album_art_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
                download_url=None
            )
            existing_track2 = Track(
                platform_id="jNQXAC9IVRw",
                platform="youtube",
                name="Me at the zoo",
                artist="jawed",
                album=None,
                album_art_url="https://i.ytimg.com/vi/jNQXAC9IVRw/hqdefault.jpg",
                download_url=None
            )
            db.session.add(existing_track1)
            db.session.add(existing_track2)
            db.session.commit()

            # Verify tracks are in DB
            initial_track_count = Track.query.count()
            assert initial_track_count == 2

            # Add a new playlist - the mock returns 3 tracks total
            error = PlaylistManagerService.add_playlists(
                "https://www.youtube.com/playlist?list=PLtest123"
            )
            
            assert error is None

            # Verify the playlist was created
            playlist = Playlist.query.first()
            assert playlist is not None
            assert playlist.platform == "youtube"
            assert playlist.name == "Test YouTube Playlist"

            # Verify no duplicate tracks were created
            # Mock returns 3 tracks, 2 already exist, so should only add 1 new track
            final_track_count = Track.query.count()
            assert final_track_count == 3, "Should have 3 total tracks (2 existing + 1 new)"
            
            # Verify all 3 tracks are associated with the playlist
            playlist_track_count = PlaylistTrack.query.filter_by(playlist_id=playlist.id).count()
            assert playlist_track_count == 3, "All 3 tracks should be associated with the playlist"

            # Verify the existing tracks are in the playlist
            playlist_tracks = PlaylistTrack.query.filter_by(playlist_id=playlist.id).all()
            track_ids = {pt.track_id for pt in playlist_tracks}
            assert existing_track1.id in track_ids
            assert existing_track2.id in track_ids

    def test_add_multiple_playlists_sharing_tracks(self, app):
        """Test adding multiple playlists that share some tracks."""
        with app.app_context():
            # Add first playlist
            error1 = PlaylistManagerService.add_playlists(
                "https://open.spotify.com/playlist/3bL14BgPXekKHep3RRdwGZ"
            )
            assert error1 is None

            # Get track count after first playlist
            track_count_after_first = Track.query.count()
            assert track_count_after_first == 2

            # Add a second playlist (different playlist but will use same mock data for simplicity)
            # In real scenario, this would be a different playlist with overlapping tracks
            # For this test, we'll add the same playlist again to verify duplicate prevention
            error2 = PlaylistManagerService.add_playlists(
                "https://open.spotify.com/playlist/3bL14BgPXekKHep3RRdwGZ"
            )
            
            # Should return error because playlist already exists
            assert error2 == "Playlist Already Added"

            # Track count should remain the same
            track_count_after_second = Track.query.count()
            assert track_count_after_second == track_count_after_first

    def test_spotify_scraper_with_existing_tracks(self, app, monkeypatch):
        """Test Spotify scraper service with existing tracks in database."""
        # Force the use of the scraper service for this test
        from app.services.platform_services.platform_services_factory import PlatformServiceFactory
        from app.services.platform_services.spotify_scraper_service import SpotifyScraperService
        from tests.mocks.mock_spotify_scraper import MockSpotifyClient, MockSpotifyBulkOperations
        
        # Mock the scraper client
        monkeypatch.setattr(
            SpotifyScraperService,
            "_get_scraper_client",
            lambda: MockSpotifyClient()
        )
        monkeypatch.setattr(
            "spotify_scraper.utils.common.SpotifyBulkOperations",
            MockSpotifyBulkOperations
        )
        # Force factory to use scraper service
        monkeypatch.setattr(
            PlatformServiceFactory, 
            "_get_spotify_service", 
            staticmethod(lambda: SpotifyScraperService)
        )
        
        with app.app_context():
            # Add sample tracks that match the scraper mock data
            # The scraper returns track IDs: 3vkQ5DAB1qQMYO4Mr9zJN6 and 0GjEhVFGZW8afUYGChu3Rr
            existing_track1 = Track(
                platform_id="3vkQ5DAB1qQMYO4Mr9zJN6",
                platform="spotify",
                name="Track One",
                artist="Artist One",
                album="Album One",
                album_art_url="https://i.scdn.co/image/ab67616d00001e02aa22899360d8ba6704732dec",
                download_url=None
            )
            db.session.add(existing_track1)
            db.session.commit()

            initial_track_count = Track.query.count()
            assert initial_track_count == 1

            # Add playlist using scraper
            error = PlaylistManagerService.add_playlists(
                "https://open.spotify.com/playlist/1zfCA5tZu2QyWINEjpzDVd"
            )
            
            assert error is None

            # Verify playlist was created
            playlist = Playlist.query.first()
            assert playlist is not None
            assert playlist.name == "Test Scraper Playlist"
            assert playlist.platform == "spotify"

            # The scraper mock returns 2 tracks, one already exists
            final_track_count = Track.query.count()
            assert final_track_count == 2, "Should have 2 total tracks (1 existing + 1 new)"

            # Verify both tracks are associated with the playlist
            playlist_track_count = PlaylistTrack.query.filter_by(playlist_id=playlist.id).count()
            assert playlist_track_count == 2

            # Verify existing track is associated with new playlist
            playlist_tracks = PlaylistTrack.query.filter_by(
                playlist_id=playlist.id,
                track_id=existing_track1.id
            ).first()
            assert playlist_tracks is not None, "Existing track should be in the playlist"
