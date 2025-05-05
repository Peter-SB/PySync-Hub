import os
import unittest
from unittest.mock import patch, MagicMock

from app.utils.file_download_utils import FileDownloadUtils
from app.models import Track


class TestFileDownloadUtils(unittest.TestCase):
    """Tests for the FileDownloadUtils class, especially the path conversion methods"""
    
    @patch('config.Config')
    def test_get_relative_path(self, mock_config):
        """Test the get_relative_path method for converting absolute paths to relative paths"""
        # Configure mock
        mock_config.DOWNLOAD_FOLDER = '/music/downloads'
        
        # Test cases: absolute paths
        test_cases = [
            # (absolute_path, expected_relative_path)
            ('/music/downloads/song.mp3', 'song.mp3'),
            ('/music/downloads/folder/song.mp3', 'folder/song.mp3'),
            ('/music/downloads/', ''),
            ('/music/other/song.mp3', '/music/other/song.mp3'),  # Outside download folder
            (None, None),  # None should return None
        ]
        
        for absolute_path, expected_result in test_cases:
            result = FileDownloadUtils.get_relative_path(absolute_path)
            self.assertEqual(result, expected_result)
        
        # Test with Windows-style paths
        mock_config.DOWNLOAD_FOLDER = 'C:\\music\\downloads'
        windows_test_cases = [
            # (absolute_path, expected_relative_path)
            ('C:\\music\\downloads\\song.mp3', 'song.mp3'),
            ('C:\\music\\downloads\\folder\\song.mp3', 'folder\\song.mp3'),
            ('D:\\other\\song.mp3', 'D:\\other\\song.mp3'),  # Different drive
        ]
        
        for absolute_path, expected_result in windows_test_cases:
            result = FileDownloadUtils.get_relative_path(absolute_path)
            self.assertEqual(result, expected_result)
    
    @patch('config.Config')
    def test_get_absolute_path(self, mock_config):
        """Test the get_absolute_path method for converting relative paths to absolute paths"""
        # Configure mock
        mock_config.DOWNLOAD_FOLDER = '/music/downloads'
        
        # Test cases: relative paths
        test_cases = [
            # (relative_path, expected_absolute_path)
            ('song.mp3', '/music/downloads/song.mp3'),
            ('folder/song.mp3', '/music/downloads/folder/song.mp3'),
            ('', '/music/downloads'),
            (None, None),  # None should return None
            ('/absolute/path/song.mp3', '/absolute/path/song.mp3'),  # Already absolute
        ]
        
        for relative_path, expected_result in test_cases:
            result = FileDownloadUtils.get_absolute_path(relative_path)
            self.assertEqual(result, expected_result)
        
        # Test with Windows-style paths
        mock_config.DOWNLOAD_FOLDER = 'C:\\music\\downloads'
        windows_test_cases = [
            # (relative_path, expected_absolute_path)
            ('song.mp3', 'C:\\music\\downloads\\song.mp3'),
            ('folder\\song.mp3', 'C:\\music\\downloads\\folder\\song.mp3'),
            ('C:\\absolute\\song.mp3', 'C:\\absolute\\song.mp3'),  # Already absolute
        ]
        
        for relative_path, expected_result in windows_test_cases:
            result = FileDownloadUtils.get_absolute_path(relative_path)
            self.assertEqual(result, expected_result)
    
    @patch('config.Config')
    @patch('os.path.isfile')
    def test_is_track_already_downloaded(self, mock_isfile, mock_config):
        """Test is_track_already_downloaded with relative paths"""
        # Configure mocks
        mock_config.DOWNLOAD_FOLDER = '/music/downloads'
        
        # Test with relative path
        mock_isfile.return_value = True
        self.assertTrue(FileDownloadUtils.is_track_already_downloaded('song.mp3'))
        mock_isfile.assert_called_with('/music/downloads/song.mp3')  # Should check the absolute path
        
        # Test when file doesn't exist
        mock_isfile.return_value = False
        self.assertFalse(FileDownloadUtils.is_track_already_downloaded('song.mp3'))
        
        # Test with absolute path
        mock_isfile.return_value = True
        self.assertTrue(FileDownloadUtils.is_track_already_downloaded('/absolute/path/song.mp3'))
        mock_isfile.assert_called_with('/absolute/path/song.mp3')
        
        # Test with None path
        self.assertFalse(FileDownloadUtils.is_track_already_downloaded(None))