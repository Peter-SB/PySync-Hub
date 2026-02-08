import pytest
from app.models import Tracklist, TracklistEntry, Track
from app.extensions import db


@pytest.mark.usefixtures("init_database")
class TestTracklistEntryModel:
    """
    Tests for the TracklistEntry database model.
    
    Tests Include:
    - Creating a tracklist entry
    - Converting entry to dictionary
    - Entry with predicted track
    - Entry with confirmed track
    - Entry relationships to tracks
    """

    def test_create_tracklist_entry(self, init_database):
        """Test creating a basic tracklist entry."""
        # Arrange
        tracklist = Tracklist(
            set_name='Test Mix',
            tracklist_string='Tracks here'
        )
        db.session.add(tracklist)
        db.session.commit()
        
        entry_data = {
            'tracklist_id': tracklist.id,
            'full_tracklist_entry': '1. Artist Name - Track Title (Remix)',
            'artist': 'Artist Name',
            'short_title': 'Track Title',
            'full_title': 'Track Title (Remix)',
            'version': 'Remix',
            'version_artist': None,
            'is_vip': False,
            'unicode_cleaned_entry': '1. Artist Name - Track Title (Remix)',
            'prefix_cleaned_entry': 'Artist Name - Track Title (Remix)',
            'is_unidentified': False,
            'favourite': False
        }
        
        # Act
        entry = TracklistEntry(**entry_data)
        db.session.add(entry)
        db.session.commit()
        
        # Assert
        assert entry.id is not None
        assert entry.tracklist_id == tracklist.id
        assert entry.artist == 'Artist Name'
        assert entry.short_title == 'Track Title'
        assert entry.full_title == 'Track Title (Remix)'
        assert entry.version == 'Remix'
        assert entry.is_vip is False
        assert entry.is_unidentified is False

    def test_tracklist_entry_to_dict(self, init_database):
        """Test converting a tracklist entry to dictionary format."""
        # Arrange
        tracklist = Tracklist(
            set_name='Test Mix',
            tracklist_string='Tracks'
        )
        db.session.add(tracklist)
        db.session.commit()
        
        entry = TracklistEntry(
            tracklist_id=tracklist.id,
            full_tracklist_entry='Artist - Track',
            artist='Artist',
            short_title='Track',
            full_title='Track'
        )
        db.session.add(entry)
        db.session.commit()
        
        # Act
        entry_dict = entry.to_dict()
        
        # Assert
        assert entry_dict['id'] == entry.id
        assert entry_dict['tracklist_id'] == tracklist.id
        assert entry_dict['artist'] == 'Artist'
        assert entry_dict['short_title'] == 'Track'
        assert entry_dict['predicted_track'] is None
        assert entry_dict['confirmed_track'] is None

    def test_tracklist_entry_with_predicted_track(self, init_database):
        """Test a tracklist entry with a predicted track match."""
        # Arrange
        tracklist = Tracklist(
            set_name='Test Mix',
            tracklist_string='Tracks'
        )
        db.session.add(tracklist)
        db.session.commit()
        
        track = Track(
            platform_id='spotify123',
            platform='spotify',
            name='Matched Track',
            artist='Matched Artist'
        )
        db.session.add(track)
        db.session.commit()
        
        entry = TracklistEntry(
            tracklist_id=tracklist.id,
            full_tracklist_entry='Matched Artist - Matched Track',
            artist='Matched Artist',
            short_title='Matched Track',
            full_title='Matched Track',
            predicted_track_id=track.id
        )
        db.session.add(entry)
        db.session.commit()
        
        # Act
        entry_dict = entry.to_dict()
        
        # Assert
        assert entry.predicted_track_id == track.id
        assert entry.predicted_track is not None
        assert entry.predicted_track.name == 'Matched Track'
        assert entry_dict['predicted_track']['name'] == 'Matched Track'

    def test_tracklist_entry_with_confirmed_track(self, init_database):
        """Test a tracklist entry with a user-confirmed track match."""
        # Arrange
        tracklist = Tracklist(
            set_name='Test Mix',
            tracklist_string='Tracks'
        )
        db.session.add(tracklist)
        db.session.commit()
        
        track = Track(
            platform_id='spotify456',
            platform='spotify',
            name='Confirmed Track',
            artist='Confirmed Artist'
        )
        db.session.add(track)
        db.session.commit()
        
        entry = TracklistEntry(
            tracklist_id=tracklist.id,
            full_tracklist_entry='Confirmed Artist - Confirmed Track',
            artist='Confirmed Artist',
            short_title='Confirmed Track',
            full_title='Confirmed Track',
            confirmed_track_id=track.id
        )
        db.session.add(entry)
        db.session.commit()
        
        # Act
        entry_dict = entry.to_dict()
        
        # Assert
        assert entry.confirmed_track_id == track.id
        assert entry.confirmed_track is not None
        assert entry.confirmed_track.name == 'Confirmed Track'
        assert entry_dict['confirmed_track']['name'] == 'Confirmed Track'

    def test_tracklist_entry_vip_and_unidentified_flags(self, init_database):
        """Test VIP and unidentified flags on tracklist entry."""
        # Arrange
        tracklist = Tracklist(
            set_name='Test Mix',
            tracklist_string='Tracks'
        )
        db.session.add(tracklist)
        db.session.commit()
        
        vip_entry = TracklistEntry(
            tracklist_id=tracklist.id,
            full_tracklist_entry='Artist - Track (VIP)',
            artist='Artist',
            short_title='Track',
            full_title='Track (VIP)',
            version='VIP',
            is_vip=True
        )
        
        id_entry = TracklistEntry(
            tracklist_id=tracklist.id,
            full_tracklist_entry='ID - ID',
            artist='ID',
            short_title='ID',
            full_title='ID',
            is_unidentified=True
        )
        
        # Act
        db.session.add(vip_entry)
        db.session.add(id_entry)
        db.session.commit()
        
        # Assert
        assert vip_entry.is_vip is True
        assert vip_entry.is_unidentified is False
        assert id_entry.is_vip is False
        assert id_entry.is_unidentified is True

    def test_tracklist_entry_relationship_to_tracklist(self, init_database):
        """Test the relationship between entry and tracklist."""
        # Arrange
        tracklist = Tracklist(
            set_name='Related Mix',
            tracklist_string='Tracks'
        )
        db.session.add(tracklist)
        db.session.commit()
        
        entry = TracklistEntry(
            tracklist_id=tracklist.id,
            full_tracklist_entry='Test Entry',
            artist='Test'
        )
        db.session.add(entry)
        db.session.commit()
        
        # Act & Assert
        assert entry.tracklist is not None
        assert entry.tracklist.id == tracklist.id
        assert entry.tracklist.set_name == 'Related Mix'
        assert tracklist.tracklist_entries[0].id == entry.id
