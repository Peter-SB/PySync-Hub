import os
import logging

from app.models import Track, Tracklist, TracklistEntry
import app.utils.tracklist_cleaning_utils as tracklist_cleaning_utils
from app.services.tracklist_services.tracklist_prediction_service import TracklistPredictionService

logger = logging.getLogger(__name__)


class TracklistImportService:
    """ Service for importing and processing tracklists. """

    @staticmethod
    def process_and_predict_tracklist(tracklist: Tracklist, database_tracks: list[Track]) -> Tracklist:
        """ Take a raw tracklist string and process it into a Tracklist with TracklistEntry including predicted matches. """
        processed_tracklist = TracklistImportService.process_tracklist(tracklist)
        tracklist_evaluated = TracklistPredictionService.predict_tracklist_matches(processed_tracklist, database_tracks)
        return tracklist_evaluated

    @staticmethod
    def process_tracklist(tracklist: Tracklist) -> Tracklist:
        """ Processes a single tracklist string into Tracklist objects. """
        split_track_list = tracklist_cleaning_utils.split_tracks(tracklist.tracklist_string)
        import_tracks = [TracklistImportService.pre_process_track(entry) for entry in split_track_list]
        
        # Filter out unidentified tracks and assign to the tracklist
        # Note: For in-memory processing, we create temporary TracklistEntry objects
        tracklist.tracklist_entries = [track for track in import_tracks if not track.is_unidentified]

        logger.info(f"Processed {len(tracklist.tracklist_entries)} tracks from tracklist.")
        return tracklist
    

    @staticmethod
    def pre_process_track(tracklist_entry: str) -> TracklistEntry:
        """ 
        Process a single tracklist entry string into a TracklistEntry object. 
        
        Returns a TracklistEntry object complete with all extracted and processed fields.
        """

        # 1. Clean unicode
        unicode_cleaned_entry = tracklist_cleaning_utils.clean_track_unicode(tracklist_entry)
        # 2. Remove prefix and label info
        prefix_cleaned_entry = tracklist_cleaning_utils.clean_track_prefix(unicode_cleaned_entry)
        label_cleaned_entry = tracklist_cleaning_utils.remove_label_info(prefix_cleaned_entry)
        # 3. Extract artist and title
        artist, full_title = tracklist_cleaning_utils.extract_artist_and_title(prefix_cleaned_entry)
        # 4. Extract title and version
        short_title, version = tracklist_cleaning_utils.extract_title_and_version(full_title)
        # 5. Identified check
        is_unidentified = tracklist_cleaning_utils.is_unidentified_track(short_title)
        # 6. Set version_artist if present in version
        version_artist = tracklist_cleaning_utils.extract_version_artist(version)
        # 7. VIP check
        is_vip = tracklist_cleaning_utils.check_for_vip(short_title) or tracklist_cleaning_utils.check_for_vip(version)   

        # Create a temporary TracklistEntry object (not persisted to DB)
        entry = TracklistEntry()
        entry.full_tracklist_entry = tracklist_entry
        entry.artist = artist
        entry.short_title = short_title
        entry.full_title = full_title
        entry.version = version
        entry.version_artist = version_artist
        entry.is_vip = is_vip
        entry.unicode_cleaned_entry = unicode_cleaned_entry
        entry.prefix_cleaned_entry = prefix_cleaned_entry
        entry.is_unidentified = is_unidentified
        entry.predicted_track_id = None
        entry.confirmed_track_id = None
        entry.favourite = False

        return entry
