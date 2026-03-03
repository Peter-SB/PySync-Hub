import pytest
from app.models import Tracklist, TracklistEntry, Track
from app.extensions import db


@pytest.mark.usefixtures("init_database")
class TestTracklistModel:
    """
    Tests for the Tracklist database model.
    
    Tests Include:
    - Creating a tracklist
    - Converting tracklist to dictionary
    - Tracklist with entries
    - Deleting tracklist cascades to entries
    """

    def test_create_tracklist(self, init_database):
        """Test creating a basic tracklist."""
        # Arrange
        tracklist_data = {
            'set_name': 'Summer Mix 2025',
            'artist': 'DJ Test',
            'tracklist_string': '1. Artist - Track One\n2. Artist - Track Two',
            'rating': 5,
            'disabled': False,
            'image_url': 'http://example.com/image.jpg',
            'custom_order': 0,
            'download_progress': 0,
            'folder_id': None
        }
        
        # Act
        tracklist = Tracklist(**tracklist_data)
        db.session.add(tracklist)
        db.session.commit()
        
        # Assert
        assert tracklist.id is not None
        assert tracklist.set_name == 'Summer Mix 2025'
        assert tracklist.artist == 'DJ Test'
        assert tracklist.rating == 5
        assert tracklist.disabled is False

    def test_tracklist_to_dict(self, init_database):
        """Test converting a tracklist to dictionary format."""
        # Arrange
        tracklist = Tracklist(
            set_name='Test Mix',
            artist='Test Artist',
            tracklist_string='Track list here',
            rating=4
        )
        db.session.add(tracklist)
        db.session.commit()
        
        # Act
        tracklist_dict = tracklist.to_dict()
        
        # Assert
        assert tracklist_dict['id'] == tracklist.id
        assert tracklist_dict['set_name'] == 'Test Mix'
        assert tracklist_dict['artist'] == 'Test Artist'
        assert tracklist_dict['rating'] == 4
        assert 'tracklist_entries' in tracklist_dict
        assert tracklist_dict['tracklist_entries'] == []

    def test_tracklist_with_entries(self, init_database):
        """Test a tracklist with multiple entries."""
        # Arrange
        tracklist = Tracklist(
            set_name='Mix with Tracks',
            tracklist_string='1. Artist - Track\n2. Artist2 - Track2'
        )
        db.session.add(tracklist)
        db.session.commit()
        
        entry1 = TracklistEntry(
            tracklist_id=tracklist.id,
            full_tracklist_entry='1. Artist - Track',
            artist='Artist',
            short_title='Track',
            full_title='Track'
        )
        entry2 = TracklistEntry(
            tracklist_id=tracklist.id,
            full_tracklist_entry='2. Artist2 - Track2',
            artist='Artist2',
            short_title='Track2',
            full_title='Track2'
        )
        db.session.add(entry1)
        db.session.add(entry2)
        db.session.commit()
        
        # Act
        tracklist_dict = tracklist.to_dict()
        
        # Assert
        assert len(tracklist.tracklist_entries) == 2
        assert len(tracklist_dict['tracklist_entries']) == 2
        assert tracklist_dict['tracklist_entries'][0]['artist'] == 'Artist'
        assert tracklist_dict['tracklist_entries'][1]['artist'] == 'Artist2'

    def test_tracklist_cascade_delete(self, init_database):
        """Test that deleting a tracklist deletes its entries."""
        # Arrange
        tracklist = Tracklist(
            set_name='To Delete',
            tracklist_string='Track list'
        )
        db.session.add(tracklist)
        db.session.commit()
        
        entry = TracklistEntry(
            tracklist_id=tracklist.id,
            full_tracklist_entry='Test Entry',
            artist='Artist'
        )
        db.session.add(entry)
        db.session.commit()
        
        tracklist_id = tracklist.id
        entry_id = entry.id
        
        # Act
        db.session.delete(tracklist)
        db.session.commit()
        
        # Assert
        assert Tracklist.query.get(tracklist_id) is None
        assert TracklistEntry.query.get(entry_id) is None

    def test_tracklist_optional_fields(self, init_database):
        """Test creating a tracklist with minimal required fields."""
        # Arrange & Act
        tracklist = Tracklist(
            set_name='Minimal Mix',
            tracklist_string='Some tracks'
        )
        db.session.add(tracklist)
        db.session.commit()
        
        # Assert
        assert tracklist.id is not None
        assert tracklist.artist is None
        assert tracklist.rating is None
        assert tracklist.folder_id is None
        assert tracklist.disabled is False
        assert tracklist.custom_order == 0
        assert tracklist.download_progress == 0
