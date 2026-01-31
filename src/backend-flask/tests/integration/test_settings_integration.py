"""Integration tests for settings routes."""
import pytest


@pytest.mark.integration
class TestSoundcloudClientIdFetchIntegration:
    """Integration tests for fetching SoundCloud client_id from the real SoundCloud homepage."""

    def test_fetch_soundcloud_client_id_happy_path(self, client):
        """Test successful fetch of SoundCloud client_id from real SoundCloud homepage."""
        response = client.get('/api/soundcloud/fetch_client_id')
        
        # Should get a successful response
        assert response.status_code == 200
        
        data = response.get_json()
        
        # Should have client_id in response
        assert 'client_id' in data
        assert data['client_id'] is not None
        assert len(data['client_id']) > 0
        
        # Should have success message
        assert 'message' in data
        assert data['message'] == 'SoundCloud client_id fetched successfully'
        
        # client_id should be alphanumeric (typical SoundCloud client_id format)
        assert data['client_id'].replace('_', '').isalnum()

        print(f"Fetched SoundCloud client_id: {data['client_id']}")
