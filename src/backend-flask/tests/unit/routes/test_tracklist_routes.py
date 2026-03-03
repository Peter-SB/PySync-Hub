import pytest
import json
from app.models import Tracklist, TracklistEntry, Track
from app.extensions import db


@pytest.mark.usefixtures("init_database")
class TestTracklistRoutes:
    """
    Tests for the tracklist API routes.
    
    Tests Include:
    - GET /api/tracklists - Get all tracklists
    - GET /api/tracklists/<id> - Get specific tracklist
    - POST /api/tracklists/add - Process tracklist with predictions
    - PUT /api/tracklists/<id> - Update tracklist
    - DELETE /api/tracklists/<id> - Delete tracklist
    """

    def test_get_all_tracklists_empty(self, app, init_database):
        """Test getting all tracklists when database is empty."""
        # Arrange
        client = app.test_client()
        
        # Act
        response = client.get('/api/tracklists')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_all_tracklists(self, app, init_database):
        """Test getting all tracklists."""
        # Arrange
        client = app.test_client()
        
        tracklist1 = Tracklist(
            set_name='Mix One',
            tracklist_string='Tracks 1'
        )
        tracklist2 = Tracklist(
            set_name='Mix Two',
            tracklist_string='Tracks 2'
        )
        db.session.add(tracklist1)
        db.session.add(tracklist2)
        db.session.commit()
        
        # Act
        response = client.get('/api/tracklists')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert any(t['set_name'] == 'Mix One' for t in data)
        assert any(t['set_name'] == 'Mix Two' for t in data)

    def test_get_tracklist_by_id(self, app, init_database):
        """Test getting a specific tracklist by ID."""
        # Arrange
        client = app.test_client()
        
        tracklist = Tracklist(
            set_name='Specific Mix',
            artist='DJ Test',
            tracklist_string='Track listing'
        )
        db.session.add(tracklist)
        db.session.commit()
        tracklist_id = tracklist.id
        
        # Act
        response = client.get(f'/api/tracklists/{tracklist_id}')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == tracklist_id
        assert data['set_name'] == 'Specific Mix'
        assert data['artist'] == 'DJ Test'

    def test_get_tracklist_by_id_not_found(self, app, init_database):
        """Test getting a non-existent tracklist."""
        # Arrange
        client = app.test_client()
        
        # Act
        response = client.get('/api/tracklists/99999')
        
        # Assert
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_add_tracklist_for_processing(self, app, init_database):
        """Test processing a tracklist string to get predictions."""
        # Arrange
        client = app.test_client()
        
        # Add some tracks to the database for matching
        track1 = Track(
            platform_id='test1',
            platform='spotify',
            name='Track One',
            artist='Artist One'
        )
        track2 = Track(
            platform_id='test2',
            platform='spotify',
            name='Track Two',
            artist='Artist Two'
        )
        db.session.add(track1)
        db.session.add(track2)
        db.session.commit()
        
        tracklist_data = {
            'set_name': 'Test Mix',
            'artist': 'DJ Test',
            'tracklist_string': '1. Artist One - Track One \n2. Artist Two - Track Two'
        }
        
        # Act
        response = client.post(
            '/api/tracklists/add',
            data=json.dumps(tracklist_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['set_name'] == 'Test Mix'
        assert data['artist'] == 'DJ Test'
        assert 'tracklist_entries' in data
        assert len(data['tracklist_entries']) == 2
        
        # Check that predictions were generated
        entry1 = data['tracklist_entries'][0]
        assert entry1['artist'] == 'Artist One'
        assert entry1['short_title'] == 'Track One'
        assert 'predicted_tracks' in entry1

    def test_add_tracklist_missing_fields(self, app, init_database):
        """Test processing tracklist with missing required fields."""
        # Arrange
        client = app.test_client()
        
        tracklist_data = {
            'set_name': 'Test Mix'
            # Missing tracklist_string
        }
        
        # Act
        response = client.post(
            '/api/tracklists/add',
            data=json.dumps(tracklist_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_update_tracklist(self, app, init_database):
        """Test updating an existing tracklist."""
        # Arrange
        client = app.test_client()
        
        tracklist = Tracklist(
            set_name='Original Name',
            tracklist_string='Original tracks',
            rating=3
        )
        db.session.add(tracklist)
        db.session.commit()
        tracklist_id = tracklist.id
        
        update_data = {
            'set_name': 'Updated Name',
            'rating': 5
        }
        
        # Act
        response = client.put(
            f'/api/tracklists/{tracklist_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['set_name'] == 'Updated Name'
        assert data['rating'] == 5

    def test_update_tracklist_not_found(self, app, init_database):
        """Test updating a non-existent tracklist."""
        # Arrange
        client = app.test_client()
        
        update_data = {
            'set_name': 'New Name'
        }
        
        # Act
        response = client.put(
            '/api/tracklists/99999',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 404

    def test_delete_tracklist(self, app, init_database):
        """Test deleting a tracklist."""
        # Arrange
        client = app.test_client()
        
        tracklist = Tracklist(
            set_name='To Delete',
            tracklist_string='Tracks'
        )
        db.session.add(tracklist)
        db.session.commit()
        tracklist_id = tracklist.id
        
        # Act
        response = client.delete(f'/api/tracklists/{tracklist_id}')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        
        # Verify it was deleted
        tracklist = Tracklist.query.get(tracklist_id)
        assert tracklist is None

    def test_delete_tracklist_not_found(self, app, init_database):
        """Test deleting a non-existent tracklist."""
        # Arrange
        client = app.test_client()
        
        # Act
        response = client.delete('/api/tracklists/99999')
        
        # Assert
        assert response.status_code == 404

    def test_process_tracklist_with_vip_tracks(self, app, init_database):
        """Test processing a tracklist containing VIP tracks."""
        # Arrange
        client = app.test_client()
        
        tracklist_data = {
            'set_name': 'VIP Mix',
            'tracklist_string': '1. Artist - Track (VIP)\n2. Artist - Normal Track'
        }
        
        # Act
        response = client.post(
            '/api/tracklists/add',
            data=json.dumps(tracklist_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        entries = data['tracklist_entries']
        assert len(entries) == 2
        assert entries[0]['is_vip'] is True
        assert entries[1]['is_vip'] is False

    def test_process_tracklist_filters_id_tracks(self, app, init_database):
        """Test that ID tracks are filtered during processing."""
        # Arrange
        client = app.test_client()
        
        tracklist_data = {
            'set_name': 'Mix with IDs',
            'tracklist_string': '1. Artist - Track\n2. ID - ID\n3. Artist - Another Track'
        }
        
        # Act
        response = client.post(
            '/api/tracklists/add',
            data=json.dumps(tracklist_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should only have 2 entries (ID track filtered out)
        assert len(data['tracklist_entries']) == 2
        assert all(not e['is_unidentified'] for e in data['tracklist_entries'])

    def test_process_tracklist_track_artist_format_with_id_track(self, app, init_database):
        """Test track-title first format parsing and filtering of unidentified ID tracks."""
        # Arrange
        client = app.test_client()

        tracklist_data = {
            'set_name': 'Track First Mix',
            'tracklist_string': '2:28 No Problem - Chase & Status\n1:20 ID - K motionz',
            'artist_first': False
        }

        # Act
        response = client.post(
            '/api/tracklists/add',
            data=json.dumps(tracklist_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['tracklist_entries']) == 1
        assert data['tracklist_entries'][0]['short_title'] == 'No Problem'
        assert data['tracklist_entries'][0]['artist'] == 'Chase & Status'
