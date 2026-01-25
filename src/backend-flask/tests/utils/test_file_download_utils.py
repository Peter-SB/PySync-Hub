import pytest
from unittest.mock import Mock, patch
from app.utils.file_download_utils import FileDownloadUtils
from config import Config


class TestFileDownloadUtilsPathPattern:
    """Test the download path pattern functionality"""
    
    def test_get_download_path_shared_pattern(self):
        """Test download path with shared pattern"""
        with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'shared'):
            track = Mock()
            track.name = "Test Song"
            track.artist = "Test Artist"
            
            subfolder, filename = FileDownloadUtils.get_download_path_for_track(track)
            
            assert subfolder == ""
            assert filename == "Test Artist - Test Song"
    
    def test_get_download_path_artist_pattern(self):
        """Test download path with artist pattern"""
        with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'artist'):
            track = Mock()
            track.name = "Test Song"
            track.artist = "Test Artist"
            
            subfolder, filename = FileDownloadUtils.get_download_path_for_track(track)
            
            assert subfolder == "Test Artist"
            assert filename == "Test Artist - Test Song"
    
    def test_get_download_path_playlist_pattern_with_playlist(self):
        """Test download path with playlist pattern when playlist is provided"""
        with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'playlist'):
            track = Mock()
            track.name = "Test Song"
            track.artist = "Test Artist"
            
            playlist = Mock()
            playlist.name = "My Playlist"
            playlist.id = 123
            
            subfolder, filename = FileDownloadUtils.get_download_path_for_track(track, playlist)
            
            assert subfolder == "My Playlist"
            assert filename == "Test Artist - Test Song_123"
    
    def test_get_download_path_playlist_pattern_without_playlist(self):
        """Test download path with playlist pattern when no playlist is provided - should fallback to shared"""
        with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'playlist'):
            track = Mock()
            track.name = "Test Song"
            track.artist = "Test Artist"
            
            subfolder, filename = FileDownloadUtils.get_download_path_for_track(track, None)
            
            # Should fallback to shared pattern
            assert subfolder == ""
            assert filename == "Test Artist - Test Song"
    
    def test_get_download_path_sanitizes_special_characters(self):
        """Test that special characters are properly sanitized in paths"""
        with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'artist'):
            track = Mock()
            track.name = "Song/With\\Special*Chars?"
            track.artist = "Artist:Name|Test"
            
            subfolder, filename = FileDownloadUtils.get_download_path_for_track(track)
            
            # Special characters should be removed
            assert "/" not in subfolder and "\\" not in subfolder
            assert "/" not in filename and "\\" not in filename
            assert "*" not in filename and "?" not in filename
    
    def test_get_download_path_handles_unicode(self):
        """Test that unicode characters are handled correctly"""
        with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'artist'):
            track = Mock()
            track.name = "Song with émojis 🎵"
            track.artist = "Артист"
            
            subfolder, filename = FileDownloadUtils.get_download_path_for_track(track)
            
            # Should not crash and return valid strings
            assert isinstance(subfolder, str)
            assert isinstance(filename, str)
    
    def test_get_download_path_handles_empty_artist(self):
        """Test behavior when artist name is empty"""
        with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'artist'):
            track = Mock()
            track.name = "Test Song"
            track.artist = ""
            
            subfolder, filename = FileDownloadUtils.get_download_path_for_track(track)
            
            assert subfolder == ""
            assert filename == " - Test Song"
    
    def test_get_download_path_handles_very_long_names(self):
        """Test that very long names are properly handled"""
        with patch.object(Config, 'DOWNLOAD_PATH_PATTERN', 'artist'):
            track = Mock()
            track.name = "A" * 300  # Very long name
            track.artist = "B" * 300  # Very long artist
            
            subfolder, filename = FileDownloadUtils.get_download_path_for_track(track)
            
            # Should be truncated to max_length (255 chars by default in sanitize_filename)
            assert len(subfolder) <= 255
            assert len(filename) <= 255


class TestFileDownloadUtilsSanitization:
    """Test sanitization functionality"""
    
    def test_sanitize_filename_removes_invalid_chars(self):
        """Test that invalid filename characters are removed"""
        input_str = 'file/name\\with*invalid?chars<>:|"'
        result = FileDownloadUtils.sanitize_filename(input_str)
        
        # All invalid chars should be removed
        for char in ['/', '\\', '*', '?', '<', '>', ':', '|', '"']:
            assert char not in result
    
    def test_sanitize_filename_preserves_valid_chars(self):
        """Test that valid characters are preserved"""
        input_str = "valid_file-name.123 test"
        result = FileDownloadUtils.sanitize_filename(input_str)
        
        assert result == input_str
    
    def test_sanitize_filename_truncates_long_names(self):
        """Test that long filenames are truncated"""
        long_name = "a" * 300
        result = FileDownloadUtils.sanitize_filename(long_name, max_length=255)
        
        assert len(result) <= 255
    
    def test_sanitize_filename_strips_trailing_spaces(self):
        """Test that trailing spaces are removed"""
        input_str = "filename with trailing spaces     "
        result = FileDownloadUtils.sanitize_filename(input_str)
        
        assert result == "filename with trailing spaces"
