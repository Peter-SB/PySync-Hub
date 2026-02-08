import logging
from datetime import datetime
from typing import List, Optional

from app.extensions import db
from app.models import Tracklist, TracklistEntry
from app.utils.db_utils import commit_with_retries

logger = logging.getLogger(__name__)


class TracklistRepository:
    @staticmethod
    def get_all_tracklists() -> List[Tracklist]:
        """Get all tracklists from the database."""
        logger.debug("Fetching all tracklists")
        return Tracklist.query.all()
    
    @staticmethod
    def get_tracklist_by_id(tracklist_id: int) -> Optional[Tracklist]:
        """Get a specific tracklist by ID."""
        logger.debug(f"Fetching tracklist with ID: {tracklist_id}")
        return Tracklist.query.get(tracklist_id)
    
    @staticmethod
    def create_tracklist(tracklist_data: dict) -> Tracklist:
        """Create a new tracklist in the database."""
        logger.info(f"Creating new tracklist: {tracklist_data.get('set_name')}")
        
        tracklist = Tracklist(
            set_name=tracklist_data.get('set_name'),
            artist=tracklist_data.get('artist'),
            tracklist_string=tracklist_data.get('tracklist_string'),
            rating=tracklist_data.get('rating'),
            disabled=tracklist_data.get('disabled', False),
            image_url=tracklist_data.get('image_url'),
            custom_order=tracklist_data.get('custom_order', 0),
            download_progress=tracklist_data.get('download_progress', 0),
            folder_id=tracklist_data.get('folder_id')
        )
        
        db.session.add(tracklist)
        commit_with_retries(db.session)
        logger.info(f"Created tracklist with ID: {tracklist.id}")
        
        return tracklist
    
    @staticmethod
    def update_tracklist(tracklist_id: int, update_data: dict) -> Optional[Tracklist]:
        """Update an existing tracklist."""
        logger.info(f"Updating tracklist ID: {tracklist_id}")
        
        tracklist = Tracklist.query.get(tracklist_id)
        if not tracklist:
            # Create if not found
            tracklist = Tracklist(
                set_name=update_data.get('set_name'),
                artist=update_data.get('artist'),
                tracklist_string=update_data.get('tracklist_string'),
                rating=update_data.get('rating'),
                disabled=update_data.get('disabled', False),
                image_url=update_data.get('image_url'),
                custom_order=update_data.get('custom_order', 0),
                download_progress=update_data.get('download_progress', 0),
                folder_id=update_data.get('folder_id')
            )
            db.session.add(tracklist)
            commit_with_retries(db.session)
            logger.info(f"Created tracklist with ID: {tracklist.id}")
            return tracklist
        
        # Update fields if provided
        if 'set_name' in update_data:
            tracklist.set_name = update_data['set_name']
        if 'artist' in update_data:
            tracklist.artist = update_data['artist']
        if 'tracklist_string' in update_data:
            tracklist.tracklist_string = update_data['tracklist_string']
        if 'rating' in update_data:
            tracklist.rating = update_data['rating']
        if 'disabled' in update_data:
            tracklist.disabled = update_data['disabled']
        if 'image_url' in update_data:
            tracklist.image_url = update_data['image_url']
        if 'custom_order' in update_data:
            tracklist.custom_order = update_data['custom_order']
        if 'download_progress' in update_data:
            tracklist.download_progress = update_data['download_progress']
        if 'folder_id' in update_data:
            tracklist.folder_id = update_data['folder_id']
        
        commit_with_retries(db.session)
        logger.info(f"Updated tracklist ID: {tracklist_id}")
        
        return tracklist
    
    @staticmethod
    def delete_tracklist(tracklist_id: int) -> bool:
        """Delete a tracklist and all its entries."""
        logger.info(f"Deleting tracklist ID: {tracklist_id}")
        
        tracklist = Tracklist.query.get(tracklist_id)
        if not tracklist:
            logger.error(f"Tracklist with ID {tracklist_id} not found")
            return False
        
        db.session.delete(tracklist)
        commit_with_retries(db.session)
        logger.info(f"Deleted tracklist ID: {tracklist_id}")
        
        return True
    
    @staticmethod
    def create_tracklist_entry(entry_data: dict) -> TracklistEntry:
        """Create a new tracklist entry."""
        logger.debug(f"Creating tracklist entry for tracklist ID: {entry_data.get('tracklist_id')}")
        
        entry = TracklistEntry(
            tracklist_id=entry_data.get('tracklist_id'),
            full_tracklist_entry=entry_data.get('full_tracklist_entry'),
            artist=entry_data.get('artist'),
            short_title=entry_data.get('short_title'),
            full_title=entry_data.get('full_title'),
            version=entry_data.get('version'),
            version_artist=entry_data.get('version_artist'),
            is_vip=entry_data.get('is_vip', False),
            unicode_cleaned_entry=entry_data.get('unicode_cleaned_entry'),
            prefix_cleaned_entry=entry_data.get('prefix_cleaned_entry'),
            is_unidentified=entry_data.get('is_unidentified', False),
            predicted_track_id=entry_data.get('predicted_track_id'),
            predicted_track_confidence=entry_data.get('predicted_track_confidence'),
            confirmed_track_id=entry_data.get('confirmed_track_id'),
            favourite=entry_data.get('favourite', False)
        )
        
        db.session.add(entry)
        commit_with_retries(db.session)
        return entry
    
    @staticmethod
    def update_tracklist_entry(entry_id: int, update_data: dict) -> Optional[TracklistEntry]:
        """Update an existing tracklist entry."""
        logger.debug(f"Updating tracklist entry ID: {entry_id}")
        
        entry = TracklistEntry.query.get(entry_id)
        if not entry:
            logger.error(f"TracklistEntry with ID {entry_id} not found")
            return None
        
        # Update fields if provided
        if 'predicted_track_id' in update_data:
            entry.predicted_track_id = update_data['predicted_track_id']
        if 'predicted_track_confidence' in update_data:
            entry.predicted_track_confidence = update_data['predicted_track_confidence']
        if 'confirmed_track_id' in update_data:
            entry.confirmed_track_id = update_data['confirmed_track_id']
        if 'favourite' in update_data:
            entry.favourite = update_data['favourite']
        
        commit_with_retries(db.session)
        
        return entry
