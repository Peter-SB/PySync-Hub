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

        response = TracklistImportService.prepare_tracklist_response(tracklist_with_predictions)
        logger.info(f"Successfully processed tracklist with {len(response['tracklist_entries'])} entries")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error("Error processing tracklist: %s", e, exc_info=True)
        return jsonify({'error': 'Failed to process tracklist', 'message': str(e)}), 500


@api.route('/api/tracklists', methods=['POST'])
def save_tracklist():    
    """
    Save a confirmed tracklist to the database. Expects a JSON body to match the Tracklist and TracklistEntry models.
    """
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
