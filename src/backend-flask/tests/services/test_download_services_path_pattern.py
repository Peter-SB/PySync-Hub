import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from app.services.download_services.spotify_download_service import SpotifyDownloadService
from app.services.download_services.soundcloud_download_service import SoundcloudDownloadService
from app.models import Track, Playlist
from config import Config


class TestDownloadServicePathPattern:
    """Test that download services use the path pattern correctly"""
    
    def test_spotify_download_track_shared_pattern(self, app, monkeypatch):
        """Test Spotify download uses shared pattern correctly"""
        with app.app_context():
            with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'shared'):
                with patch.object(Config, 'DOWNLOAD_FOLDER', '/tmp/downloads'):
                    track = Mock(spec=Track)
                    track.name = "Test Song"
                    track.artist = "Test Artist"
                    track.download_url = "https://www.youtube.com/watch?v=test"
                    track.album = "Test Album"
                    track.album_art_url = None
                    
                    # Mock the download operations
                    with patch('app.services.download_services.spotify_download_service.YoutubeDL') as mock_ytdl:
                        with patch('os.path.exists', return_value=False):
                            with patch('app.utils.file_download_utils.FileDownloadUtils.embed_track_metadata'):
                                with patch('os.makedirs'):
                                    with patch('app.services.download_services.spotify_download_service.db.session'):
                                        with patch('app.services.download_services.spotify_download_service.commit_with_retries'):
                                            # Setup mock YoutubeDL
                                            mock_ydl_instance = MagicMock()
                                            mock_ydl_instance.extract_info.return_value = {
                                                'title': 'Test Video Title'
                                            }
                                            mock_ytdl.return_value.__enter__.return_value = mock_ydl_instance
                                            
                                            # Call the download method
                                            SpotifyDownloadService.download_track_with_ytdlp(track)
                                            
                                            # Verify the file path doesn't include a subfolder
                                            assert track.set_download_location.called
                                            call_args = track.set_download_location.call_args[0][0]
                                            # Should be in the root download folder, not in a subfolder
                                            assert '/tmp/downloads/' in call_args
                                            # Should not have extra path separators indicating subfolders
                                            path_parts = call_args.replace('/tmp/downloads/', '').split('/')
                                            assert len(path_parts) == 1  # Only filename, no subfolder
    
    def test_spotify_download_track_artist_pattern(self, app, monkeypatch):
        """Test Spotify download uses artist pattern correctly"""
        with app.app_context():
            with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'artist'):
                with patch.object(Config, 'DOWNLOAD_FOLDER', '/tmp/downloads'):
                    track = Mock(spec=Track)
                    track.name = "Test Song"
                    track.artist = "Test Artist"
                    track.download_url = "https://www.youtube.com/watch?v=test"
                    track.album = "Test Album"
                    track.album_art_url = None
                    
                    # Mock the download operations
                    with patch('app.services.download_services.spotify_download_service.YoutubeDL') as mock_ytdl:
                        with patch('os.path.exists', return_value=False):
                            with patch('app.utils.file_download_utils.FileDownloadUtils.embed_track_metadata'):
                                with patch('os.makedirs') as mock_makedirs:
                                    with patch('app.services.download_services.spotify_download_service.db.session'):
                                        with patch('app.services.download_services.spotify_download_service.commit_with_retries'):
                                            # Setup mock YoutubeDL
                                            mock_ydl_instance = MagicMock()
                                            mock_ydl_instance.extract_info.return_value = {
                                                'title': 'Test Video Title'
                                            }
                                            mock_ytdl.return_value.__enter__.return_value = mock_ydl_instance
                                            
                                            # Call the download method
                                            SpotifyDownloadService.download_track_with_ytdlp(track)
                                            
                                            # Verify the artist subfolder was created
                                            mock_makedirs.assert_called()
                                            makedirs_call = mock_makedirs.call_args[0][0]
                                            assert 'Test Artist' in makedirs_call
                                            
                                            # Verify the file path includes the artist folder
                                            assert track.set_download_location.called
                                            call_args = track.set_download_location.call_args[0][0]
                                            assert '/tmp/downloads/Test Artist/' in call_args
    
    def test_spotify_download_track_playlist_pattern(self, app, monkeypatch):
        """Test Spotify download uses playlist pattern correctly"""
        with app.app_context():
            with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'playlist'):
                with patch.object(Config, 'DOWNLOAD_FOLDER', '/tmp/downloads'):
                    track = Mock(spec=Track)
                    track.name = "Test Song"
                    track.artist = "Test Artist"
                    track.download_url = "https://www.youtube.com/watch?v=test"
                    track.album = "Test Album"
                    track.album_art_url = None
                    
                    playlist = Mock(spec=Playlist)
                    playlist.name = "My Playlist"
                    playlist.id = 42
                    
                    # Mock the download operations
                    with patch('app.services.download_services.spotify_download_service.YoutubeDL') as mock_ytdl:
                        with patch('os.path.exists', return_value=False):
                            with patch('app.utils.file_download_utils.FileDownloadUtils.embed_track_metadata'):
                                with patch('os.makedirs') as mock_makedirs:
                                    with patch('app.services.download_services.spotify_download_service.db.session'):
                                        with patch('app.services.download_services.spotify_download_service.commit_with_retries'):
                                            # Setup mock YoutubeDL
                                            mock_ydl_instance = MagicMock()
                                            mock_ydl_instance.extract_info.return_value = {
                                                'title': 'Test Video Title'
                                            }
                                            mock_ytdl.return_value.__enter__.return_value = mock_ydl_instance
                                            
                                            # Call the download method with playlist
                                            SpotifyDownloadService.download_track_with_ytdlp(track, playlist)
                                            
                                            # Verify the playlist subfolder was created
                                            mock_makedirs.assert_called()
                                            makedirs_call = mock_makedirs.call_args[0][0]
                                            assert 'My Playlist' in makedirs_call
                                            
                                            # Verify the file path includes the playlist folder and unique ID
                                            assert track.set_download_location.called
                                            call_args = track.set_download_location.call_args[0][0]
                                            assert '/tmp/downloads/My Playlist/' in call_args
                                            assert '_42.mp3' in call_args  # Playlist ID appended
    
    def test_soundcloud_download_track_artist_pattern(self, app, monkeypatch):
        """Test SoundCloud download uses artist pattern correctly"""
        with app.app_context():
            with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'artist'):
                with patch.object(Config, 'DOWNLOAD_FOLDER', '/tmp/downloads'):
                    track = Mock(spec=Track)
                    track.name = "Test Song"
                    track.artist = "Test Artist"
                    track.download_url = "https://soundcloud.com/test/song"
                    track.album = None
                    track.album_art_url = None
                    
                    # Mock the download operations
                    with patch('app.services.download_services.soundcloud_download_service.YoutubeDL') as mock_ytdl:
                        with patch('os.path.exists', return_value=False):
                            with patch('app.utils.file_download_utils.FileDownloadUtils.embed_track_metadata'):
                                with patch('os.makedirs') as mock_makedirs:
                                    with patch('app.services.download_services.soundcloud_download_service.db.session'):
                                        with patch('app.services.download_services.soundcloud_download_service.commit_with_retries'):
                                            # Setup mock YoutubeDL
                                            mock_ydl_instance = MagicMock()
                                            mock_ytdl.return_value.__enter__.return_value = mock_ydl_instance
                                            
                                            # Call the download method
                                            SoundcloudDownloadService.download_track_with_ytdlp(track)
                                            
                                            # Verify the artist subfolder was created
                                            mock_makedirs.assert_called()
                                            makedirs_call = mock_makedirs.call_args[0][0]
                                            assert 'Test Artist' in makedirs_call
                                            
                                            # Verify the file path includes the artist folder
                                            assert track.set_download_location.called
                                            call_args = track.set_download_location.call_args[0][0]
                                            assert '/tmp/downloads/Test Artist/' in call_args
    
    def test_download_track_skips_if_already_exists(self, app, monkeypatch):
        """Test that download is skipped if file already exists at the expected location"""
        with app.app_context():
            with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'artist'):
                with patch.object(Config, 'DOWNLOAD_FOLDER', '/tmp/downloads'):
                    track = Mock(spec=Track)
                    track.name = "Test Song"
                    track.artist = "Test Artist"
                    track.download_url = "https://www.youtube.com/watch?v=test"
                    track.album = "Test Album"
                    track.album_art_url = None
                    
                    # Mock that file exists
                    with patch('os.path.exists', return_value=True):
                        with patch('os.makedirs'):  # Mock makedirs to avoid actual directory creation
                            with patch('app.services.download_services.spotify_download_service.YoutubeDL') as mock_ytdl:
                                with patch('app.services.download_services.spotify_download_service.db.session'):
                                    with patch('app.services.download_services.spotify_download_service.commit_with_retries'):
                                        # Setup mock YoutubeDL for extract_info only (no download)
                                        mock_ydl_instance = MagicMock()
                                        mock_ydl_instance.extract_info.return_value = {
                                            'title': 'Test Video Title'
                                        }
                                        mock_ytdl.return_value.__enter__.return_value = mock_ydl_instance
                                        
                                        # Call the download method
                                        SpotifyDownloadService.download_track_with_ytdlp(track)
                                        
                                        # Verify download was not called, only extract_info
                                        assert mock_ydl_instance.download.call_count == 0
                                        # But set_download_location should still be called
                                        assert track.set_download_location.called


class TestDownloadServiceEdgeCases:
    """Test edge cases in download services"""
    
    def test_download_with_special_characters_in_names(self, app):
        """Test download with special characters in track/artist names"""
        with app.app_context():
            with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'artist'):
                with patch.object(Config, 'DOWNLOAD_FOLDER', '/tmp/downloads'):
                    track = Mock(spec=Track)
                    track.name = "Test/Song*With:Special?"
                    track.artist = "Test\\Artist|Name"
                    track.download_url = "https://www.youtube.com/watch?v=test"
                    track.album = "Test Album"
                    track.album_art_url = None
                    
                    with patch('app.services.download_services.spotify_download_service.YoutubeDL') as mock_ytdl:
                        with patch('os.path.exists', return_value=False):
                            with patch('app.utils.file_download_utils.FileDownloadUtils.embed_track_metadata'):
                                with patch('os.makedirs') as mock_makedirs:
                                    with patch('app.services.download_services.spotify_download_service.db.session'):
                                        with patch('app.services.download_services.spotify_download_service.commit_with_retries'):
                                            mock_ydl_instance = MagicMock()
                                            mock_ydl_instance.extract_info.return_value = {
                                                'title': 'Test Video Title'
                                            }
                                            mock_ytdl.return_value.__enter__.return_value = mock_ydl_instance
                                            
                                            # Should not raise an exception
                                            SpotifyDownloadService.download_track_with_ytdlp(track)
                                            
                                            # Verify makedirs was called with sanitized path
                                            mock_makedirs.assert_called()
                                            makedirs_call = mock_makedirs.call_args[0][0]
                                            # Special chars should be removed (except path separators)
                                            # Get just the folder name part, not the full path
                                            folder_name = makedirs_call.split('/')[-1]
                                            for char in ['\\', '*', '?', ':', '|']:
                                                assert char not in folder_name
