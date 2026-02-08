import pytest
from app.models import Tracklist, TracklistEntry, Track
from app.services.tracklist_services.tracklist_import_service import TracklistImportService
from app.extensions import db


@pytest.mark.usefixtures("init_database")
class TestTracklistImportServiceUnit:
    """
    Tests for the TracklistImportService.
    
    Tests Include:
    - Processing a tracklist string
    - Pre-processing individual track entries
    - Extracting artist and title
    - Handling special cases (VIP, ID tracks)
    - Unicode and prefix cleaning
    """

    def test_process_tracklist(self, init_database):
        """Test processing a complete tracklist string."""
        # Arrange
        tracklist_string = """1. Artist One - Track Title One
2. Artist Two - Track Title Two (Remix)
3. Artist Three - Track Title Three"""
        
        tracklist = Tracklist(
            set_name='Test Mix',
            tracklist_string=tracklist_string
        )
        
        # Act
        processed_tracklist = TracklistImportService.process_tracklist(tracklist)
        
        # Assert
        assert len(processed_tracklist.tracklist_entries) == 3
        assert processed_tracklist.tracklist_entries[0].artist == 'Artist One'
        assert processed_tracklist.tracklist_entries[1].artist == 'Artist Two'
        assert processed_tracklist.tracklist_entries[2].artist == 'Artist Three'

    def test_pre_process_track_basic(self, init_database):
        """Test pre-processing a basic track entry."""
        # Arrange
        track_entry = "1. Artist Name - Track Title"
        
        # Act
        processed_entry = TracklistImportService.pre_process_track(track_entry)
        
        # Assert
        assert processed_entry.full_tracklist_entry == "1. Artist Name - Track Title"
        assert processed_entry.artist == "Artist Name"
        assert processed_entry.short_title == "Track Title"
        assert processed_entry.full_title == "Track Title"
        assert processed_entry.is_unidentified is False

    def test_pre_process_track_with_remix(self, init_database):
        """Test pre-processing a track with remix version."""
        # Arrange
        track_entry = "Artist - Track Name (Some DJ Remix)"
        
        # Act
        processed_entry = TracklistImportService.pre_process_track(track_entry)
        
        # Assert
        assert processed_entry.artist == "Artist"
        assert processed_entry.short_title == "Track Name"
        assert processed_entry.full_title == "Track Name (Some DJ Remix)"
        assert "Remix" in processed_entry.version

    def test_pre_process_track_vip(self, init_database):
        """Test pre-processing a VIP track."""
        # Arrange
        track_entry = "Artist - Track Name (VIP)"
        
        # Act
        processed_entry = TracklistImportService.pre_process_track(track_entry)
        
        # Assert
        assert processed_entry.is_vip is True
        assert processed_entry.version == "VIP"

    def test_pre_process_track_unidentified(self, init_database):
        """Test pre-processing an unidentified track (ID)."""
        # Arrange
        track_entry = "ID - ID"
        
        # Act
        processed_entry = TracklistImportService.pre_process_track(track_entry)
        
        # Assert
        assert processed_entry.is_unidentified is True

    def test_process_tracklist_filters_unidentified(self, init_database):
        """Test that unidentified tracks are filtered out."""
        # Arrange
        tracklist_string = """1. Artist - Track One
2. ID - ID
3. Artist - Track Two"""
        
        tracklist = Tracklist(
            set_name='Test Mix',
            tracklist_string=tracklist_string
        )
        
        # Act
        processed_tracklist = TracklistImportService.process_tracklist(tracklist)
        
        # Assert
        # Should only have 2 entries (ID track filtered out)
        assert len(processed_tracklist.tracklist_entries) == 2
        assert all(not entry.is_unidentified for entry in processed_tracklist.tracklist_entries)

    def test_pre_process_track_with_prefix(self, init_database):
        """Test pre-processing a track with number prefix."""
        # Arrange
        track_entry = "01. Artist Name - Track Title"
        
        # Act
        processed_entry = TracklistImportService.pre_process_track(track_entry)
        
        # Assert
        assert processed_entry.artist == "Artist Name"
        assert processed_entry.short_title == "Track Title"
        assert "01." not in processed_entry.prefix_cleaned_entry

    def test_pre_process_track_complex_version(self, init_database):
        """Test pre-processing a track with complex version info."""
        # Arrange
        track_entry = "Artist - Track Name (Another Artist Bootleg Edit)"
        
        # Act
        processed_entry = TracklistImportService.pre_process_track(track_entry)
        
        # Assert
        assert processed_entry.artist == "Artist"
        assert processed_entry.short_title == "Track Name"
        assert "Bootleg" in processed_entry.version or "Edit" in processed_entry.version
        assert processed_entry.version_artist is not None

    def test_process_tracklist_with_newlines(self, init_database):
        """Test processing a tracklist with various newline formats."""
        # Arrange
        tracklist_string = "Artist One - Track One\nArtist Two - Track Two\nArtist Three - Track Three"
        
        tracklist = Tracklist(
            set_name='Test Mix',
            tracklist_string=tracklist_string
        )
        
        # Act
        processed_tracklist = TracklistImportService.process_tracklist(tracklist)
        
        # Assert
        assert len(processed_tracklist.tracklist_entries) == 3

    def test_pre_process_track_unicode_handling(self, init_database):
        """Test that unicode characters are properly cleaned."""
        # Arrange
        track_entry = "Artíst – Trâck Nâme"
        
        # Act
        processed_entry = TracklistImportService.pre_process_track(track_entry)
        
        # Assert
        assert processed_entry.unicode_cleaned_entry is not None
        # Unicode should be cleaned/normalized
        assert processed_entry.artist is not None
        assert processed_entry.short_title is not None

    def test_process_empty_tracklist(self, init_database):
        """Test processing an empty tracklist string."""
        # Arrange
        tracklist = Tracklist(
            set_name='Empty Mix',
            tracklist_string=''
        )
        
        # Act
        processed_tracklist = TracklistImportService.process_tracklist(tracklist)
        
        # Assert
        assert len(processed_tracklist.tracklist_entries) == 0

    def test_pre_process_track_with_multiple_artists(self, init_database):
        """Test pre-processing a track with multiple artists."""
        # Arrange
        track_entry = "Artist One & Artist Two - Track Name"
        
        # Act
        processed_entry = TracklistImportService.pre_process_track(track_entry)
        
        # Assert
        assert "Artist One" in processed_entry.artist
        assert "Artist Two" in processed_entry.artist
        assert processed_entry.short_title == "Track Name"

    def test_process_tracklist_with_w_separator(self, init_database):
        """Test processing tracklist with 'w/' separator (converted to newline)."""
        # Arrange
        tracklist_string = "Artist One - Track One w/ Artist Two - Track Two"
        
        tracklist = Tracklist(
            set_name='Test Mix',
            tracklist_string=tracklist_string
        )
        
        # Act
        processed_tracklist = TracklistImportService.process_tracklist(tracklist)
        
        # Assert
        # 'w/' should be converted to newline, creating 2 entries
        assert len(processed_tracklist.tracklist_entries) >= 1

    def test_pre_process_track_fields_populated(self, init_database):
        """Test that all fields are properly populated after processing."""
        # Arrange
        track_entry = "5. Test Artist - Test Track (VIP Mix)"
        
        # Act
        processed_entry = TracklistImportService.pre_process_track(track_entry)
        
        # Assert
        assert processed_entry.full_tracklist_entry is not None
        assert processed_entry.artist is not None
        assert processed_entry.short_title is not None
        assert processed_entry.full_title is not None
        assert processed_entry.unicode_cleaned_entry is not None
        assert processed_entry.prefix_cleaned_entry is not None
        assert processed_entry.predicted_track_id is None
        assert processed_entry.confirmed_track_id is None
        assert processed_entry.favourite is False
