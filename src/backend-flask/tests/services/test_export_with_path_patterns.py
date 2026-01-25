import pytest
from unittest.mock import Mock, patch
from app.models import Track, Playlist, PlaylistTrack
from app.services.export_services.export_rekorbox_service import RekordboxExportService
from config import Config


class TestExportWithPathPatterns:
    """Test that export works correctly with different download path patterns"""
    
    def test_export_works_with_relative_paths(self, app):
        """Test that export correctly resolves relative paths to absolute paths"""
        with app.app_context():
            # Create a track with a relative path
            track = Track()
            track.id = 1
            track.name = "Test Song"
            track.artist = "Test Artist"
            track.album = "Test Album"
            track.platform = "spotify"
            track.platform_id = "spotify123"
            # Set a relative path
            track.download_location = "Test Artist/Test Artist - Test Song.mp3"
            
            # Create a playlist with this track
            playlist = Playlist()
            playlist.id = 1
            playlist.name = "Test Playlist"
            playlist.platform = "spotify"
            playlist.external_id = "playlist123"
            playlist.disabled = False
            
            playlist_track = PlaylistTrack()
            playlist_track.playlist_id = 1
            playlist_track.track_id = 1
            playlist_track.track_order = 0
            playlist_track.playlist = playlist
            playlist_track.track = track
            
            playlist.tracks = [playlist_track]
            
            # Mock the database query
            with patch('app.models.Playlist.query') as mock_query:
                mock_query.filter_by.return_value.all.return_value = [playlist]
                
                with patch('os.path.exists', return_value=True):
                    with patch('os.makedirs'):
                        with patch('xml.etree.ElementTree.ElementTree.write'):
                            # Call the export function
                            export_path = RekordboxExportService.generate_rekordbox_xml_from_db()
                            
                            # Verify export path was returned
                            assert export_path is not None
                            
                            # The track's absolute_download_path should be computed correctly
                            absolute_path = track.absolute_download_path
                            assert absolute_path is not None
                            assert Config.DOWNLOAD_FOLDER in absolute_path
                            assert "Test Artist" in absolute_path
    
    def test_export_with_artist_pattern_paths(self, app):
        """Test export with tracks organized by artist"""
        with app.app_context():
            # Create tracks with artist-based paths
            tracks = []
            for i in range(3):
                track = Track()
                track.id = i + 1
                track.name = f"Song {i+1}"
                track.artist = f"Artist {i+1}"
                track.album = "Test Album"
                track.platform = "spotify"
                track.platform_id = f"spotify{i+1}"
                # Artist pattern: artist folder
                track.download_location = f"Artist {i+1}/Artist {i+1} - Song {i+1}.mp3"
                tracks.append(track)
            
            playlist = Playlist()
            playlist.id = 1
            playlist.name = "Test Playlist"
            playlist.platform = "spotify"
            playlist.external_id = "playlist123"
            playlist.disabled = False
            
            playlist_tracks = []
            for idx, track in enumerate(tracks):
                pt = PlaylistTrack()
                pt.playlist_id = 1
                pt.track_id = track.id
                pt.track_order = idx
                pt.playlist = playlist
                pt.track = track
                playlist_tracks.append(pt)
            
            playlist.tracks = playlist_tracks
            
            with patch('app.models.Playlist.query') as mock_query:
                mock_query.filter_by.return_value.all.return_value = [playlist]
                
                with patch('os.path.exists', return_value=True):
                    with patch('os.makedirs'):
                        with patch('xml.etree.ElementTree.ElementTree.write'):
                            # Export should work
                            export_path = RekordboxExportService.generate_rekordbox_xml_from_db()
                            assert export_path is not None
                            
                            # All tracks should have valid absolute paths
                            for track in tracks:
                                absolute_path = track.absolute_download_path
                                assert absolute_path is not None
                                assert track.artist in absolute_path
    
    def test_export_with_playlist_pattern_paths(self, app):
        """Test export with tracks organized by playlist (with duplication)"""
        with app.app_context():
            # Same track in two different playlists with different paths
            track = Track()
            track.id = 1
            track.name = "Shared Song"
            track.artist = "Shared Artist"
            track.album = "Test Album"
            track.platform = "spotify"
            track.platform_id = "spotify123"
            # First playlist path
            track.download_location = "Playlist 1/Shared Artist - Shared Song_1.mp3"
            
            playlist1 = Playlist()
            playlist1.id = 1
            playlist1.name = "Playlist 1"
            playlist1.platform = "spotify"
            playlist1.external_id = "playlist1"
            playlist1.disabled = False
            
            pt1 = PlaylistTrack()
            pt1.playlist_id = 1
            pt1.track_id = 1
            pt1.track_order = 0
            pt1.playlist = playlist1
            pt1.track = track
            
            playlist1.tracks = [pt1]
            
            # Second playlist would have a different file (with _2)
            playlist2 = Playlist()
            playlist2.id = 2
            playlist2.name = "Playlist 2"
            playlist2.platform = "spotify"
            playlist2.external_id = "playlist2"
            playlist2.disabled = False
            
            # Note: In reality, for playlist pattern, we'd have duplicate Track records
            # with different download_location values. Here we're just testing
            # that the export logic handles the paths correctly
            
            with patch('app.models.Playlist.query') as mock_query:
                mock_query.filter_by.return_value.all.return_value = [playlist1]
                
                with patch('os.path.exists', return_value=True):
                    with patch('os.makedirs'):
                        with patch('xml.etree.ElementTree.ElementTree.write'):
                            # Export should work
                            export_path = RekordboxExportService.generate_rekordbox_xml_from_db()
                            assert export_path is not None
                            
                            # Track path should be resolved correctly
                            absolute_path = track.absolute_download_path
                            assert absolute_path is not None
                            assert "Playlist 1" in absolute_path
