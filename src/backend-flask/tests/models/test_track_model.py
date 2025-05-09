import os
import unittest
from unittest.mock import patch, MagicMock

from app.models import Track
from app.utils.file_download_utils import FileDownloadUtils


class TestTrackModel(unittest.TestCase):
    """Tests for the Track model, focusing on the path handling methods"""
    
    @patch('app.utils.file_download_utils.FileDownloadUtils.get_absolute_path')
    def test_absolute_download_path(self, mock_get_absolute_path):
        """Test the absolute_download_path property"""
        # Configure mock
        mock_get_absolute_path.return_value = '/absolute/path/song.mp3'
        
        # Create a track with a relative path
        track = Track()
        track.download_location = 'song.mp3'
        
        # Test getting absolute path
        self.assertEqual(track.absolute_download_path, '/absolute/path/song.mp3')
        mock_get_absolute_path.assert_called_with('song.mp3')
        
        # Test with None path
        track.download_location = None
        self.assertIsNone(track.absolute_download_path)
    
    @patch('app.utils.file_download_utils.FileDownloadUtils.get_relative_path')
    def test_set_download_location(self, mock_get_relative_path):
        """Test the set_download_location method"""
        # Configure mock
        mock_get_relative_path.return_value = 'song.mp3'
        
        # Create a track and set an absolute path
        track = Track()
        track.set_download_location('/absolute/path/song.mp3')
        
        # Verify that the track's download_location was set to the relative path
        self.assertEqual(track.download_location, 'song.mp3')
        mock_get_relative_path.assert_called_with('/absolute/path/song.mp3')
        
        # Test with None path
        track.set_download_location(None)
        self.assertIsNone(track.download_location)
    
    @patch('app.utils.file_download_utils.FileDownloadUtils.get_absolute_path')
    def test_to_dict_with_absolute_path(self, mock_get_absolute_path):
        """Test that the to_dict method returns absolute paths"""
        # Configure mock
        mock_get_absolute_path.return_value = '/absolute/path/song.mp3'
        
        # Create a track with test data
        track = Track()
        track.name = 'Test Song'
        track.artist = 'Test Artist'
        track.platform = 'spotify'
        track.platform_id = '12345'
        track.download_location = 'song.mp3'
        
        # Get dictionary representation
        track_dict = track.to_dict()
        
        # Verify that download_location is the absolute path
        self.assertEqual(track_dict['download_location'], '/absolute/path/song.mp3')
        mock_get_absolute_path.assert_called_with('song.mp3')