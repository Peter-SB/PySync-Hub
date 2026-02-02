import logging
from typing import Optional

from flask import Blueprint, request, jsonify, current_app

from app.extensions import db, socketio
from app.models import Track, Tracklist, TracklistEntry
from app.repositories.tracklist_repository import TracklistRepository
from app.routes import api
from app.services.tracklist_services.tracklist_import_service import TracklistImportService
from app.services.tracklist_services.tracklist_prediction_service import TracklistPredictionService
from app.utils.db_utils import commit_with_retries
from config import Config

logger = logging.getLogger(__name__)

@api.route('/api/tracklists', methods=['GET'])
def get_tracklists():
    """Get all tracklists from the database."""
    try:
        tracklists = TracklistRepository.get_all_tracklists()
        tracklists_data = [t.to_dict() for t in tracklists]
        return jsonify(tracklists_data), 200
    except Exception as e:
        logger.error("Error fetching tracklists: %s", e, exc_info=True)
        return jsonify({'error': str(e)}), 500


@api.route('/api/tracklists/add', methods=['POST'])
def add_tracklist():    
    """
    Process a tracklist string and return predictions for user confirmation.
    
    Expects JSON body with:
    - tracklist_string: The raw tracklist text
    - set_name: Name of the set/tracklist
    - Track Format (optional): whether artist - track, or track - artist
    
    Returns the processed tracklist with predicted track matches.
    """
    try:
        data = request.get_json()
        
        if not data or 'tracklist_string' not in data or 'set_name' not in data:
            return jsonify({'error': 'Missing required fields: tracklist_string and set_name'}), 400
        
        logger.info(f"Processing tracklist: {data.get('set_name')}")
        
        # Create Tracklist object and save
        tracklist = Tracklist(
            set_name=data.get('set_name'),
            artist=data.get('artist'),
            tracklist_string=data.get('tracklist_string'),
            rating=data.get('rating'),
            image_url=data.get('image_url'),
            folder_id=data.get('folder_id')
        )
        
        # Process the tracklist and predict
        database_tracks = Track.query.all()
        tracklist_with_predictions = TracklistImportService.process_and_predict_tracklist(tracklist, database_tracks)

        # Save to db
        db.session.add(tracklist_with_predictions)
        commit_with_retries(db.session)

        response = TracklistImportService._prepare_tracklist_response(tracklist_with_predictions)
        logger.info(f"Successfully processed tracklist with {len(response['tracklist_entries'])} entries")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error("Error processing tracklist: %s", e, exc_info=True)
        return jsonify({'error': 'Failed to process tracklist', 'message': str(e)}), 500


# @api.route('/api/tracklists', methods=['POST'])
def save_tracklist():    
    """
    Save a confirmed tracklist to the database. Expects a JSON body to match the Tracklist and TracklistEntry models.
    """
    return
    try:
        data = request.get_json()
        
        if not data or 'set_name' not in data or 'tracklist_string' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        logger.info(f"Saving tracklist: {data.get('set_name')}")
        
        # Create the tracklist in the database
        tracklist_data = {
            'set_name': data.get('set_name'),
            'artist': data.get('artist'),
            'tracklist_string': data.get('tracklist_string'),
            'rating': data.get('rating'),
            'disabled': data.get('disabled', False),
            'image_url': data.get('image_url'),
            'custom_order': data.get('custom_order', 0),
            'download_progress': data.get('download_progress', 0),
            'folder_id': data.get('folder_id')
        }
        
        tracklist = TracklistRepository.create_tracklist(tracklist_data)
        
        # Create tracklist entries if provided
        if 'tracklist_entries' in data and data['tracklist_entries']:
            for entry_data in data['tracklist_entries']:
                entry_dict = {
                    'tracklist_id': tracklist.id,
                    'full_tracklist_entry': entry_data.get('full_tracklist_entry'),
                    'artist': entry_data.get('artist'),
                    'short_title': entry_data.get('short_title'),
                    'full_title': entry_data.get('full_title'),
                    'version': entry_data.get('version'),
                    'version_artist': entry_data.get('version_artist'),
                    'is_vip': entry_data.get('is_vip', False),
                    'unicode_cleaned_entry': entry_data.get('unicode_cleaned_entry'),
                    'prefix_cleaned_entry': entry_data.get('prefix_cleaned_entry'),
                    'is_unidentified': entry_data.get('is_unidentified', False),
                    'predicted_track_id': entry_data.get('predicted_track_id'),
                    'predicted_track_confidence': entry_data.get('predicted_track_confidence'),
                    'confirmed_track_id': entry_data.get('confirmed_track_id'),
                    'favourite': entry_data.get('favourite', False)
                }
                TracklistRepository.create_tracklist_entry(entry_dict)
        
        # Fetch the complete tracklist with all entries
        saved_tracklist = TracklistRepository.get_tracklist_by_id(tracklist.id)
        
        logger.info(f"Successfully saved tracklist ID: {tracklist.id}")
        return jsonify(saved_tracklist.to_dict()), 201
        
    except Exception as e:
        logger.error("Error saving tracklist: %s", e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to save tracklist', 'message': str(e)}), 500


@api.route('/api/tracklists/<int:tracklist_id>', methods=['GET'])
def get_tracklist(tracklist_id):
    """Get a specific tracklist by ID."""
    try:
        tracklist = TracklistRepository.get_tracklist_by_id(tracklist_id)
        if not tracklist:
            return jsonify({'error': 'Tracklist not found'}), 404
        
        return jsonify(tracklist.to_dict()), 200
    except Exception as e:
        logger.error("Error fetching tracklist: %s", e, exc_info=True)
        return jsonify({'error': 'Failed to fetch tracklist', 'message': str(e)}), 500


@api.route('/api/tracklists/<int:tracklist_id>', methods=['PUT'])
def update_tracklist(tracklist_id):
    """Update an existing tracklist."""
    try:
        data = request.get_json()
        
        tracklist = TracklistRepository.update_tracklist(tracklist_id, data)
        if not tracklist:
            return jsonify({'error': 'Tracklist not found'}), 404
        
        # Update entries if provided
        if 'tracklist_entries' in data:
            for entry_data in data['tracklist_entries']:
                if 'id' in entry_data:
                    # Update existing entry
                    TracklistRepository.update_tracklist_entry(entry_data['id'], entry_data)
        
        # Fetch the updated tracklist
        updated_tracklist = TracklistRepository.get_tracklist_by_id(tracklist_id)
        return jsonify(updated_tracklist.to_dict()), 200
        
    except Exception as e:
        logger.error("Error updating tracklist: %s", e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to update tracklist', 'message': str(e)}), 500


@api.route('/api/tracklists/<int:tracklist_id>/refresh', methods=['POST'])
def refresh_tracklist(tracklist_id):
    """Re-run predictions for unconfirmed entries in a tracklist."""
    # todo: fix this to match closer to add logic. Maybe rerun the whole tracklist import process with confirmed tracks skipped/stripped from the string
    try:
        tracklist = TracklistRepository.get_tracklist_by_id(tracklist_id)
        if not tracklist:
            return jsonify({'error': 'Tracklist not found'}), 404

        database_tracks = Track.query.all()
        updated_entries = 0

        # Attempt to reprocess the tracklist string to align entries by order
        processed_entries = None
        try:
            temp_tracklist = Tracklist(
                set_name=tracklist.set_name,
                artist=tracklist.artist,
                tracklist_string=tracklist.tracklist_string,
                rating=tracklist.rating,
                image_url=tracklist.image_url,
                folder_id=tracklist.folder_id
            )
            processed = TracklistImportService.process_tracklist(temp_tracklist)
            processed_entries = processed.tracklist_entries
        except Exception as e:
            logger.warning("Failed to reprocess tracklist string for %s: %s", tracklist_id, e)

        entries = list(tracklist.tracklist_entries)
        entries.sort(key=lambda entry: (entry.order_index is None, entry.order_index if entry.order_index is not None else entry.id))

        if processed_entries and len(processed_entries) == len(entries):
            for entry, processed_entry in zip(entries, processed_entries):
                if entry.confirmed_track_id:
                    continue

                entry.full_tracklist_entry = processed_entry.full_tracklist_entry
                entry.artist = processed_entry.artist
                entry.short_title = processed_entry.short_title
                entry.full_title = processed_entry.full_title
                entry.version = processed_entry.version
                entry.version_artist = processed_entry.version_artist
                entry.is_vip = processed_entry.is_vip
                entry.unicode_cleaned_entry = processed_entry.unicode_cleaned_entry
                entry.prefix_cleaned_entry = processed_entry.prefix_cleaned_entry
                entry.is_unidentified = processed_entry.is_unidentified

                top_candidates = TracklistPredictionService.find_top_track_matches(
                    processed_entry,
                    database_tracks,
                    top_n=1,
                    min_score=0.0
                )

                if top_candidates:
                    top_track, top_score = top_candidates[0]
                    entry.predicted_track_id = top_track.id
                    entry.predicted_track_confidence = top_score
                else:
                    entry.predicted_track_id = None
                    entry.predicted_track_confidence = None

                updated_entries += 1
        else:
            if processed_entries is not None:
                logger.warning(
                    "Tracklist %s entry count mismatch (existing=%s, processed=%s); using existing entries",
                    tracklist_id,
                    len(entries),
                    len(processed_entries)
                )

            for entry in entries:
                if entry.confirmed_track_id:
                    continue

                top_candidates = TracklistPredictionService.find_top_track_matches(
                    entry,
                    database_tracks,
                    top_n=1,
                    min_score=0.0
                )

                if top_candidates:
                    top_track, top_score = top_candidates[0]
                    entry.predicted_track_id = top_track.id
                    entry.predicted_track_confidence = top_score
                else:
                    entry.predicted_track_id = None
                    entry.predicted_track_confidence = None

                updated_entries += 1

        commit_with_retries(db.session)
        logger.info("Refreshed tracklist %s with %s updated entries", tracklist_id, updated_entries)
        return jsonify(tracklist.to_dict()), 200

    except Exception as e:
        logger.error("Error refreshing tracklist: %s", e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to refresh tracklist', 'message': str(e)}), 500


@api.route('/api/tracklists/<int:tracklist_id>', methods=['DELETE'])
def delete_tracklist(tracklist_id):
    """Delete a tracklist."""
    try:
        success = TracklistRepository.delete_tracklist(tracklist_id)
        if not success:
            return jsonify({'error': 'Tracklist not found'}), 404
        
        return jsonify({'message': 'Tracklist deleted successfully'}), 200
    except Exception as e:
        logger.error("Error deleting tracklist: %s", e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to delete tracklist', 'message': str(e)}), 500
