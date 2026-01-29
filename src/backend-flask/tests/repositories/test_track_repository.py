import pytest
from datetime import datetime, date
from app.models import Playlist, Track, PlaylistTrack
from app.repositories.track_repository import TrackRepository
from app.extensions import db


@pytest.mark.usefixtures("init_database")
class TestTrackRepository:
    """
    Tests for the TrackRepository class.
    
    Tests Include:
    - Removing tracks before a date limit
    - Removing excess tracks when track limit is set
    - Getting track added date
    - Getting track index in playlist
    """

    def test_remove_tracks_before_date(self, init_database):
        # Create a playlist
        playlist = Playlist(
            name="Test Playlist",
            platform="spotify",
            external_id="123",
            track_count=3
        )
        db.session.add(playlist)
        db.session.commit()

        # Create some tracks
        tracks = [
            Track(
                platform_id=f"track_{i}",
                platform="spotify",
                name=f"Track {i}",
                artist=f"Artist {i}"
            ) for i in range(3)
        ]
        for track in tracks:
            db.session.add(track)
        db.session.commit()

        # Add tracks to playlist with different added dates
        dates = [
            datetime(2023, 1, 1),
            datetime(2024, 1, 1),
            datetime(2024, 2, 1)
        ]
        for i, (track, added_date) in enumerate(zip(tracks, dates)):
            playlist_track = PlaylistTrack(
                playlist_id=playlist.id,
                track_id=track.id,
                track_order=i,
                added_on=added_date
            )
            db.session.add(playlist_track)
        db.session.commit()

        # Set date limit to 2024-01-15
        date_limit = date(2024, 1, 15)
        
        # Remove tracks before date limit
        remaining_tracks = TrackRepository.remove_tracks_before_date(playlist, date_limit)
        
        # Verify only tracks added after the date limit remain
        assert len(remaining_tracks) == 1
        assert all(pt.added_on.date() >= date_limit for pt in playlist.tracks)

    def test_remove_tracks_before_date_no_limit(self, init_database):
        # Create a playlist
        playlist = Playlist(
            name="Test Playlist",
            platform="spotify",
            external_id="123",
            track_count=3
        )
        db.session.add(playlist)
        db.session.commit()

        # Create some tracks
        tracks = [
            Track(
                platform_id=f"track_{i}",
                platform="spotify",
                name=f"Track {i}",
                artist=f"Artist {i}"
            ) for i in range(3)
        ]
        for track in tracks:
            db.session.add(track)
        db.session.commit()

        # Add tracks to playlist
        for i, track in enumerate(tracks):
            playlist_track = PlaylistTrack(
                playlist_id=playlist.id,
                track_id=track.id,
                track_order=i,
                added_on=datetime(2024, 1, 1)
            )
            db.session.add(playlist_track)
        db.session.commit()

        # Try to remove tracks with no date limit
        remaining_tracks = TrackRepository.remove_tracks_before_date(playlist, None)
        
        # Verify all tracks remain
        assert len(remaining_tracks) == 3
        assert len(playlist.tracks) == 3

    def test_remove_excess_tracks(self, init_database):
        # Create a playlist
        playlist = Playlist(
            name="Test Playlist",
            platform="spotify",
            external_id="123",
            track_count=5
        )
        db.session.add(playlist)
        db.session.commit()

        # Create some tracks
        tracks = [
            Track(
                platform_id=f"track_{i}",
                platform="spotify",
                name=f"Track {i}",
                artist=f"Artist {i}"
            ) for i in range(5)
        ]
        for track in tracks:
            db.session.add(track)
        db.session.commit()

        # Add tracks to playlist
        for i, track in enumerate(tracks):
            playlist_track = PlaylistTrack(
                playlist_id=playlist.id,
                track_id=track.id,
                track_order=i,
                added_on=datetime(2024, 1, 1)
            )
            db.session.add(playlist_track)
        db.session.commit()

        # Set track limit to 3
        new_track_limit = 3
        
        # Remove excess tracks
        remaining_tracks = TrackRepository.remove_excess_tracks(playlist, new_track_limit)
        
        # Verify only the first 3 tracks remain
        assert len(remaining_tracks) == 3
        assert len(playlist.tracks) == 3
        assert all(pt.track_order < new_track_limit for pt in playlist.tracks)

    def test_remove_excess_tracks_no_excess(self, init_database):
        # Create a playlist
        playlist = Playlist(
            name="Test Playlist",
            platform="spotify",
            external_id="123",
            track_count=3
        )
        db.session.add(playlist)
        db.session.commit()

        # Create some tracks
        tracks = [
            Track(
                platform_id=f"track_{i}",
                platform="spotify",
                name=f"Track {i}",
                artist=f"Artist {i}"
            ) for i in range(3)
        ]
        for track in tracks:
            db.session.add(track)
        db.session.commit()

        # Add tracks to playlist
        for i, track in enumerate(tracks):
            playlist_track = PlaylistTrack(
                playlist_id=playlist.id,
                track_id=track.id,
                track_order=i,
                added_on=datetime(2024, 1, 1)
            )
            db.session.add(playlist_track)
        db.session.commit()

        # Set track limit to 5 (more than current tracks)
        new_track_limit = 5
        
        # Try to remove excess tracks
        remaining_tracks = TrackRepository.remove_excess_tracks(playlist, new_track_limit)
        
        # Verify all tracks remain
        assert len(remaining_tracks) == 3
        assert len(playlist.tracks) == 3

    def test_get_track_added_on(self, init_database):
        # Create a playlist and track
        playlist = Playlist(
            name="Test Playlist",
            platform="spotify",
            external_id="123",
            track_count=1
        )
        db.session.add(playlist)
        db.session.commit()

        track = Track(
            platform_id="track_1",
            platform="spotify",
            name="Track 1",
            artist="Artist 1"
        )
        db.session.add(track)
        db.session.commit()

        # Add track to playlist with a specific date
        added_date = datetime(2024, 1, 1)
        playlist_track = PlaylistTrack(
            playlist_id=playlist.id,
            track_id=track.id,
            track_order=0,
            added_on=added_date
        )
        db.session.add(playlist_track)
        db.session.commit()

        # Get track added date
        track_date = TrackRepository.get_track_added_on(playlist, playlist_track)
        
        # Verify the date
        assert track_date == added_date.date()

    def test_get_track_added_on_no_date(self, init_database):
        # Create a playlist and track
        playlist = Playlist(
            name="Test Playlist",
            platform="spotify",
            external_id="123",
            track_count=1
        )
        db.session.add(playlist)
        db.session.commit()

        track = Track(
            platform_id="track_1",
            platform="spotify",
            name="Track 1",
            artist="Artist 1"
        )
        db.session.add(track)
        db.session.commit()

        # Add track to playlist without a date
        playlist_track = PlaylistTrack(
            playlist_id=playlist.id,
            track_id=track.id,
            track_order=0
        )
        db.session.add(playlist_track)
        db.session.commit()

        # Get track added date
        track_date = TrackRepository.get_track_added_on(playlist, playlist_track)
        
        # Verify no date is returned
        assert track_date is None

    def test_get_track_index(self, init_database):
        # Create a playlist
        playlist = Playlist(
            name="Test Playlist",
            platform="spotify",
            external_id="123",
            track_count=3
        )
        db.session.add(playlist)
        db.session.commit()

        # Create some tracks
        tracks = [
            Track(
                platform_id=f"track_{i}",
                platform="spotify",
                name=f"Track {i}",
                artist=f"Artist {i}"
            ) for i in range(3)
        ]
        for track in tracks:
            db.session.add(track)
        db.session.commit()

        # Add tracks to playlist
        for i, track in enumerate(tracks):
            playlist_track = PlaylistTrack(
                playlist_id=playlist.id,
                track_id=track.id,
                track_order=i,
                added_on=datetime(2024, 1, 1)
            )
            db.session.add(playlist_track)
        db.session.commit()

        # Get index of middle track
        track_index = TrackRepository.get_track_index(playlist, tracks[1])
        
        # Verify the index
        assert track_index == 1

    def test_get_track_index_not_found(self, init_database):
        # Create a playlist
        playlist = Playlist(
            name="Test Playlist",
            platform="spotify",
            external_id="123",
            track_count=1
        )
        db.session.add(playlist)
        db.session.commit()

        # Create a track that's not in the playlist
        track = Track(
            platform_id="track_1",
            platform="spotify",
            name="Track 1",
            artist="Artist 1"
        )
        db.session.add(track)
        db.session.commit()

        # Try to get index of track not in playlist
        track_index = TrackRepository.get_track_index(playlist, track)
        
        # Verify no index is returned
        assert track_index is None 

    def test_get_existing_spotify_ids_happy_path(self, init_database):
        # Arrange: create spotify and non-spotify tracks
        spotify_tracks = [
            Track(platform_id="sp_1", platform="spotify", name="Track 1", artist="Artist 1"),
            Track(platform_id="sp_2", platform="spotify", name="Track 2", artist="Artist 2"),
        ]
        other_track = Track(
            platform_id="yt_1",
            platform="youtube",
            name="YT Track 1",
            artist="YT Artist 1",
        )
        db.session.add_all(spotify_tracks + [other_track])
        db.session.commit()

        track_ids = ["sp_1", "sp_2", "sp_3"]

        # Act
        existing_ids = TrackRepository.get_existing_spotify_ids(track_ids)

        # Assert
        assert set(existing_ids) == {"sp_1", "sp_2"}

    def test_get_existing_spotify_ids_empty_input(self, init_database):
        # Arrange
        track_ids = []

        # Act
        existing_ids = TrackRepository.get_existing_spotify_ids(track_ids)

        # Assert
        assert existing_ids == []

    def test_get_existing_spotify_ids_no_matches(self, init_database):
        # Arrange: create spotify tracks not in query
        tracks = [
            Track(platform_id="sp_10", platform="spotify", name="Track 10", artist="Artist 10"),
            Track(platform_id="sp_11", platform="spotify", name="Track 11", artist="Artist 11"),
        ]
        db.session.add_all(tracks)
        db.session.commit()

        track_ids = ["sp_1", "sp_2"]

        # Act
        existing_ids = TrackRepository.get_existing_spotify_ids(track_ids)

        # Assert
        assert existing_ids == []

    def test_get_existing_spotify_ids_ignores_other_platforms(self, init_database):
        # Arrange: only non-spotify tracks exist
        tracks = [
            Track(platform_id="sp_1", platform="youtube", name="YT 1", artist="A1"),
            Track(platform_id="sp_2", platform="soundcloud", name="SC 2", artist="A2"),
        ]
        db.session.add_all(tracks)
        db.session.commit()

        track_ids = ["sp_1", "sp_2"]

        # Act
        existing_ids = TrackRepository.get_existing_spotify_ids(track_ids)

        # Assert
        assert existing_ids == []

    def test_get_track_by_platform_id_happy_path(self, init_database):
        # Create and add a track
        track = Track(
            platform_id="sp_123",
            platform="spotify",
            name="Test Track",
            artist="Test Artist"
        )
        db.session.add(track)
        db.session.commit()

        # Retrieve the track by platform_id
        found = TrackRepository.get_track_by_platform_id("sp_123")
        assert found is not None
        assert found.platform_id == "sp_123"
        assert found.name == "Test Track"