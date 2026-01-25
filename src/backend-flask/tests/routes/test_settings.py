import pytest
import yaml
import os
from unittest.mock import patch, mock_open
from config import Config


class TestSettingsAPI:
    """Test the settings API endpoints"""
    
    def test_get_settings_returns_all_fields(self, client, app):
        """Test GET /api/settings returns all settings including download_path_pattern"""
        with app.app_context():
            # Create mock settings data
            mock_settings = {
                'SPOTIFY_CLIENT_ID': 'test_client_id',
                'SPOTIFY_CLIENT_SECRET': 'test_client_secret',
                'SOUNDCLOUD_CLIENT_ID': 'test_soundcloud_id',
                'DOWNLOAD_PATH_PATTERN': 'artist'
            }
            
            with patch('builtins.open', mock_open(read_data=yaml.safe_dump(mock_settings))):
                response = client.get('/api/settings')
                
                assert response.status_code == 200
                data = response.get_json()
                
                assert data['spotify_client_id'] == 'test_client_id'
                assert data['spotify_client_secret'] == 'test_client_secret'
                assert data['soundcloud_client_id'] == 'test_soundcloud_id'
                assert data['download_path_pattern'] == 'artist'
                assert 'download_folder' in data
    
    def test_get_settings_defaults_to_shared(self, client, app):
        """Test GET /api/settings defaults to 'shared' if pattern not set"""
        with app.app_context():
            mock_settings = {
                'SPOTIFY_CLIENT_ID': 'test_client_id',
                'SPOTIFY_CLIENT_SECRET': 'test_client_secret',
                'SOUNDCLOUD_CLIENT_ID': 'test_soundcloud_id'
            }
            
            with patch('builtins.open', mock_open(read_data=yaml.safe_dump(mock_settings))):
                response = client.get('/api/settings')
                
                assert response.status_code == 200
                data = response.get_json()
                
                assert data['download_path_pattern'] == 'shared'
    
    def test_post_settings_saves_download_path_pattern(self, client, app):
        """Test POST /api/settings saves the download_path_pattern"""
        with app.app_context():
            test_data = {
                'spotify_client_id': 'new_client_id',
                'spotify_client_secret': 'new_client_secret',
                'soundcloud_client_id': 'new_soundcloud_id',
                'download_path_pattern': 'playlist'
            }
            
            written_data = {}
            
            def mock_write(file_obj, data):
                written_data.update(yaml.safe_load(data))
            
            with patch('builtins.open', mock_open()) as m:
                # Configure the mock to capture written data
                m.return_value.write.side_effect = lambda x: written_data.update(yaml.safe_load(x)) if x else None
                
                with patch('yaml.safe_dump') as mock_dump:
                    def capture_dump(data, file):
                        written_data.update(data)
                    
                    mock_dump.side_effect = capture_dump
                    
                    with patch.object(Config, 'load_settings'):
                        response = client.post('/api/settings', json=test_data)
                    
                    assert response.status_code == 200
                    assert written_data['DOWNLOAD_PATH_PATTERN'] == 'playlist'
                    assert written_data['SPOTIFY_CLIENT_ID'] == 'new_client_id'
    
    def test_post_settings_defaults_to_shared_if_not_provided(self, client, app):
        """Test POST /api/settings defaults to 'shared' if pattern not provided"""
        with app.app_context():
            test_data = {
                'spotify_client_id': 'new_client_id',
                'spotify_client_secret': 'new_client_secret',
                'soundcloud_client_id': 'new_soundcloud_id'
            }
            
            written_data = {}
            
            with patch('builtins.open', mock_open()) as m:
                with patch('yaml.safe_dump') as mock_dump:
                    def capture_dump(data, file):
                        written_data.update(data)
                    
                    mock_dump.side_effect = capture_dump
                    
                    with patch.object(Config, 'load_settings'):
                        response = client.post('/api/settings', json=test_data)
                    
                    assert response.status_code == 200
                    assert written_data['DOWNLOAD_PATH_PATTERN'] == 'shared'


class TestConfigDownloadPathPattern:
    """Test the Config class download path pattern handling"""
    
    def test_config_loads_download_path_pattern(self):
        """Test that Config.load_settings loads the download_path_pattern"""
        mock_settings = {
            'SPOTIFY_CLIENT_ID': 'test_id',
            'SPOTIFY_CLIENT_SECRET': 'test_secret',
            'SOUNDCLOUD_CLIENT_ID': 'test_soundcloud',
            'DOWNLOAD_PATH_PATTERN': 'artist'
        }
        
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(mock_settings))):
            Config.load_settings()
            
            assert Config.DOWNLOAD_PATH_PATTERN == 'artist'
    
    def test_config_defaults_to_shared_if_not_set(self):
        """Test that Config defaults to 'shared' if pattern not in settings"""
        mock_settings = {
            'SPOTIFY_CLIENT_ID': 'test_id',
            'SPOTIFY_CLIENT_SECRET': 'test_secret',
            'SOUNDCLOUD_CLIENT_ID': 'test_soundcloud'
        }
        
        with patch('builtins.open', mock_open(read_data=yaml.safe_dump(mock_settings))):
            Config.load_settings()
            
            assert Config.DOWNLOAD_PATH_PATTERN == 'shared'
