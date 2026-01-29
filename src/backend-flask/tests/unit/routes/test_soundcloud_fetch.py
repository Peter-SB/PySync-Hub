import pytest
from unittest.mock import patch, MagicMock
import json


@pytest.mark.usefixtures("client", "init_database")
class TestSoundCloudClientIdFetch:
    """Tests for fetching SoundCloud client_id from homepage."""

    def test_fetch_soundcloud_client_id_success(self, client):
        """Test successful fetch of SoundCloud client_id."""
        # Mock HTML response from SoundCloud
        mock_html = '''
        <html>
            <script>
                window.__sc_hydration = [
                    {"hydratable": "apiClient", "data": { "id": "MNAdchLuJ5WsWAIfPAFVcs0qcO3aGNcT", "other": "data" }},
                    {"hydratable": "other", "data": {}}
                ];
            </script>
        </html>
        '''
        
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        with patch('requests.get', return_value=mock_response):
            response = client.get('/api/soundcloud/fetch_client_id')
            data = json.loads(response.data)
            
            assert response.status_code == 200
            assert 'client_id' in data
            assert data['client_id'] == 'MNAdchLuJ5WsWAIfPAFVcs0qcO3aGNcT'
            assert data['message'] == 'SoundCloud client_id fetched successfully'

    def test_fetch_soundcloud_client_id_not_found(self, client):
        """Test when client_id pattern is not found in HTML."""
        mock_html = '<html><body>No client ID here</body></html>'
        
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        with patch('requests.get', return_value=mock_response):
            response = client.get('/api/soundcloud/fetch_client_id')
            data = json.loads(response.data)
            
            assert response.status_code == 500
            assert 'error' in data
            assert 'Failed to extract client_id' in data['error']

    def test_fetch_soundcloud_client_id_network_error(self, client):
        """Test when network request fails."""
        with patch('requests.get', side_effect=Exception('Network error')):
            response = client.get('/api/soundcloud/fetch_client_id')
            data = json.loads(response.data)
            
            assert response.status_code == 500
            assert 'error' in data
            assert 'Unexpected error' in data['error']
