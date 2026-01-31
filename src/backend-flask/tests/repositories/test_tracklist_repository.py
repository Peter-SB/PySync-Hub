import pytest
from datetime import datetime
from app.models import Tracklist, TracklistEntry, Track
from app.repositories.tracklist_repository import TracklistRepository
from app.extensions import db


@pytest.mark.usefixtures("init_database")
class TestTracklistRepository:
    """
    Tests for the TracklistRepository.
    
    Tests Include:
    - Getting all tracklists
    - Getting tracklist by ID
    - Creating a tracklist
    - Updating a tracklist
    - Deleting a tracklist
    - Creating tracklist entries
    - Updating tracklist entries
    """

    def test_get_all_tracklists(self, init_database):
        """Test retrieving all tracklists from the database."""
        # Arrange
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
        tracklists = TracklistRepository.get_all_tracklists()
        
        # Assert
        assert len(tracklists) == 2
        assert tracklists[0].set_name in ['Mix One', 'Mix Two']
        assert tracklists[1].set_name in ['Mix One', 'Mix Two']

    def test_get_tracklist_by_id(self, init_database):
        """Test retrieving a specific tracklist by ID."""
        # Arrange
        tracklist = Tracklist(
            set_name='Specific Mix',
            tracklist_string='Specific tracks'
        )
        db.session.add(tracklist)
        db.session.commit()
        tracklist_id = tracklist.id
        
        # Act
        retrieved_tracklist = TracklistRepository.get_tracklist_by_id(tracklist_id)
        
        # Assert
        assert retrieved_tracklist is not None
        assert retrieved_tracklist.id == tracklist_id
        assert retrieved_tracklist.set_name == 'Specific Mix'

    def test_get_tracklist_by_id_not_found(self, init_database):
        """Test retrieving a non-existent tracklist returns None."""
        # Arrange & Act
        retrieved_tracklist = TracklistRepository.get_tracklist_by_id(99999)
        
        # Assert
        assert retrieved_tracklist is None

    def test_create_tracklist(self, init_database):
        """Test creating a new tracklist."""
        # Arrange
        tracklist_data = {
            'set_name': 'New Mix',
            'artist': 'DJ New',
            'tracklist_string': '1. Track One\n2. Track Two',
            'rating': 5,
            'disabled': False,
            'image_url': 'http://example.com/image.jpg',
            'custom_order': 1,
            'download_progress': 0,
            'folder_id': None
        }
        
        # Act
        created_tracklist = TracklistRepository.create_tracklist(tracklist_data)
        
        # Assert
        assert created_tracklist.id is not None
        assert created_tracklist.set_name == 'New Mix'
        assert created_tracklist.artist == 'DJ New'
        assert created_tracklist.rating == 5
        assert created_tracklist.custom_order == 1
        
        # Verify it's in the database
        db_tracklist = Tracklist.query.get(created_tracklist.id)
        assert db_tracklist is not None
        assert db_tracklist.set_name == 'New Mix'

    def test_update_tracklist(self, init_database):
        """Test updating an existing tracklist."""
        # Arrange
        tracklist = Tracklist(
            set_name='Original Name',
            artist='Original Artist',
            tracklist_string='Original tracks',
            rating=3
        )
        db.session.add(tracklist)
        db.session.commit()
        tracklist_id = tracklist.id
        
        update_data = {
            'set_name': 'Updated Name',
            'artist': 'Updated Artist',
            'rating': 5,
            'disabled': True
        }
        
        # Act
        updated_tracklist = TracklistRepository.update_tracklist(tracklist_id, update_data)
        
        # Assert
        assert updated_tracklist is not None
        assert updated_tracklist.set_name == 'Updated Name'
        assert updated_tracklist.artist == 'Updated Artist'
        assert updated_tracklist.rating == 5
        assert updated_tracklist.disabled is True
        
        # Verify in database
        db_tracklist = Tracklist.query.get(tracklist_id)
        assert db_tracklist.set_name == 'Updated Name'

    def test_update_tracklist_partial_update(self, init_database):
        """Test updating only some fields of a tracklist."""
        # Arrange
        tracklist = Tracklist(
            set_name='Original',
            artist='Original Artist',
            tracklist_string='Original tracks',
            rating=3
        )
        db.session.add(tracklist)
        db.session.commit()
        tracklist_id = tracklist.id
        
        # Act - only update rating
        updated_tracklist = TracklistRepository.update_tracklist(
            tracklist_id, 
            {'rating': 5}
        )
        
        # Assert
        assert updated_tracklist.rating == 5
        assert updated_tracklist.set_name == 'Original'
        assert updated_tracklist.artist == 'Original Artist'

    def test_update_tracklist_not_found(self, init_database):
        """Test updating a non-existent tracklist returns None."""
        # Arrange & Act
        updated_tracklist = TracklistRepository.update_tracklist(
            99999, 
            {'set_name': 'New Name'}
        )
        
        # Assert
        assert updated_tracklist is None

    def test_delete_tracklist(self, init_database):
        """Test deleting a tracklist."""
        # Arrange
        tracklist = Tracklist(
            set_name='To Delete',
            tracklist_string='Tracks'
        )
        db.session.add(tracklist)
        db.session.commit()
        tracklist_id = tracklist.id
        
        # Act
        result = TracklistRepository.delete_tracklist(tracklist_id)
        
        # Assert
        assert result is True
        assert Tracklist.query.get(tracklist_id) is None

    def test_delete_tracklist_not_found(self, init_database):
        """Test deleting a non-existent tracklist returns False."""
        # Arrange & Act
        result = TracklistRepository.delete_tracklist(99999)
        
        # Assert
        assert result is False

    def test_create_tracklist_entry(self, init_database):
        """Test creating a tracklist entry."""
        # Arrange
        tracklist = Tracklist(
            set_name='Test Mix',
            tracklist_string='Tracks'
        )
        db.session.add(tracklist)
        db.session.commit()
        
        entry_data = {
            'tracklist_id': tracklist.id,
            'full_tracklist_entry': 'Artist - Track Name',
            'artist': 'Artist',
            'short_title': 'Track Name',
            'full_title': 'Track Name',
            'version': None,
            'version_artist': None,
            'is_vip': False,
            'unicode_cleaned_entry': 'Artist - Track Name',
            'prefix_cleaned_entry': 'Artist - Track Name',
            'is_unidentified': False,
            'predicted_track_id': None,
            'confirmed_track_id': None,
            'favourite': False
        }
        
        # Act
        created_entry = TracklistRepository.create_tracklist_entry(entry_data)
        
        # Assert
        assert created_entry.id is not None
        assert created_entry.tracklist_id == tracklist.id
        assert created_entry.artist == 'Artist'
        assert created_entry.short_title == 'Track Name'
        
        # Verify in database
        db_entry = TracklistEntry.query.get(created_entry.id)
        assert db_entry is not None
        assert db_entry.artist == 'Artist'

    def test_update_tracklist_entry(self, init_database):
        """Test updating a tracklist entry."""
        # Arrange
        tracklist = Tracklist(
            set_name='Test Mix',
            tracklist_string='Tracks'
        )
        db.session.add(tracklist)
        db.session.commit()
        
        track = Track(
            platform_id='test123',
            platform='spotify',
            name='Test Track',
            artist='Test Artist'
        )
        db.session.add(track)
        db.session.commit()
        
        entry = TracklistEntry(
            tracklist_id=tracklist.id,
            full_tracklist_entry='Test - Track',
            artist='Test',
            short_title='Track',
            full_title='Track'
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id
        
        update_data = {
            'predicted_track_id': track.id,
            'favourite': True
        }
        
        # Act
        updated_entry = TracklistRepository.update_tracklist_entry(entry_id, update_data)
        
        # Assert
        assert updated_entry is not None
        assert updated_entry.predicted_track_id == track.id
        assert updated_entry.favourite is True
        
        # Verify in database
        db_entry = TracklistEntry.query.get(entry_id)
        assert db_entry.predicted_track_id == track.id
        assert db_entry.favourite is True

    def test_update_tracklist_entry_not_found(self, init_database):
        """Test updating a non-existent entry returns None."""
        # Arrange & Act
        updated_entry = TracklistRepository.update_tracklist_entry(
            99999,
            {'favourite': True}
        )
        
        # Assert
        assert updated_entry is None

    def test_create_tracklist_with_minimal_fields(self, init_database):
        """Test creating a tracklist with only required fields."""
        # Arrange
        tracklist_data = {
            'set_name': 'Minimal Mix',
            'tracklist_string': 'Some tracks'
        }
        
        # Act
        created_tracklist = TracklistRepository.create_tracklist(tracklist_data)
        
        # Assert
        assert created_tracklist.id is not None
        assert created_tracklist.set_name == 'Minimal Mix'
        assert created_tracklist.artist is None
        assert created_tracklist.rating is None
        assert created_tracklist.disabled is False
        assert created_tracklist.custom_order == 0
