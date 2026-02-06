import logging
from typing import Optional
from types import SimpleNamespace

from flask import Blueprint, request, jsonify, current_app

from app.extensions import db, socketio
from app.models import Track, Tracklist, TracklistEntry
from app.repositories.tracklist_repository import TracklistRepository
from app.repositories.track_repository import TrackRepository
from app.routes import api
from app.services.tracklist_services.tracklist_import_service import TracklistImportService
from app.services.tracklist_services.tracklist_prediction_service import FeatureScores, TracklistPredictionService
from app.services.platform_services.platform_services_factory import PlatformServiceFactory
from app.services.download_services.download_service_factory import DownloadServiceFactory
from app.utils.db_utils import commit_with_retries
from app.utils import feature_scoring_utils
from config import Config


logger = logging.getLogger(__name__)

@api.route('/api/tracklists/search-track', methods=['GET'])
def search_track():
    """Search for tracks by name or artist. Query params: q (query), limit (max results per platform, default 3)"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Missing query parameter q'}), 400
    
    limit = request.args.get('limit', 3, type=int)
    if limit < 1 or limit > 10:
        return jsonify({'error': 'Limit must be between 1 and 10'}), 400
    
    try:
        tracks = TracklistImportService.search_for_track_on_all_platforms(query, limit=limit)
        return jsonify(tracks), 200
    except Exception as e:
        logger.error(f"Error searching tracks: {e}", exc_info=True)
        return jsonify({'error': 'Failed to search tracks', 'message': str(e)}), 500


@api.route('/api/tracklists/search-tracklist-entry', methods=['POST'])
def search_tracklist_entry():
    """
    Search for a tracklist entry on the platforms and return the results and the confidence scores.

    Expects JSON body with either:
    - tracklist_entry_id: Existing TracklistEntry ID
    - tracklist_entry: Raw tracklist entry string (e.g., "Artist - Title (Remix)")

    Optional:
    - limit: Max results to return (default 5, min 1, max 10)
    """
    data = request.get_json() or {}

    try:
        limit = int(data.get('limit', 5))
    except (TypeError, ValueError):
        return jsonify({'error': 'Limit must be an integer'}), 400

    if limit < 1 or limit > 10:
        return jsonify({'error': 'Limit must be between 1 and 10'}), 400

    tracklist_entry_id = data.get('tracklist_entry_id')
    raw_entry = data.get('tracklist_entry') or data.get('full_tracklist_entry')

    if not tracklist_entry_id and not raw_entry:
        return jsonify({'error': 'Provide tracklist_entry_id or tracklist_entry'}), 400

    try:
        if tracklist_entry_id:
            entry = TracklistEntry.query.get(tracklist_entry_id)
            if not entry:
                return jsonify({'error': 'Tracklist entry not found'}), 404

            working_entry = TracklistEntry()
            working_entry.full_tracklist_entry = entry.full_tracklist_entry
            working_entry.artist = entry.artist
            working_entry.short_title = entry.short_title
            working_entry.full_title = entry.full_title
            working_entry.version = entry.version
            working_entry.version_artist = entry.version_artist
            working_entry.is_vip = entry.is_vip
            working_entry.unicode_cleaned_entry = entry.unicode_cleaned_entry
            working_entry.prefix_cleaned_entry = entry.prefix_cleaned_entry
            working_entry.is_unidentified = entry.is_unidentified
        else:
            working_entry = TracklistImportService.pre_process_track(raw_entry)

        query_parts = []
        if working_entry.artist:
            query_parts.append(working_entry.artist)
        if working_entry.full_title:
            query_parts.append(working_entry.full_title)
        elif working_entry.short_title:
            query_parts.append(working_entry.short_title)
        if not query_parts and working_entry.full_tracklist_entry:
            query_parts.append(working_entry.full_tracklist_entry)

        query = " - ".join(query_parts).strip()
        found_tracks = TracklistImportService.search_for_track_on_all_platforms(query, limit=limit)

        predicted_tracks = []
        for track in found_tracks:
            candidate = SimpleNamespace(
                name=track.get('name') or "",
                artist=track.get('artist') or ""
            )
            feature_scores = FeatureScores(**feature_scoring_utils.calculate_feature_scores_tracks(working_entry, candidate))
            predicted_tracks.append({
                'track': track,
                'confidence': TracklistPredictionService.predict(feature_scores)
            })

        predicted_tracks.sort(key=lambda item: item['confidence'], reverse=True)

        return jsonify({'predicted_tracks': predicted_tracks}), 200
    except Exception as e:
        logger.error("Error searching tracklist entry: %s", e, exc_info=True)
        return jsonify({'error': 'Failed to search tracklist entry', 'message': str(e)}), 500


@api.route('/api/tracklists/resolve-track-url', methods=['POST'])
def resolve_track_url():
    """
    Resolve a track URL to platform track details and confidence for a tracklist entry.

    Expects JSON body with:
    - url: Track URL (Spotify/SoundCloud/YouTube)
    - tracklist_entry_id (optional): Existing TracklistEntry ID
    - tracklist_entry / full_tracklist_entry (optional): Raw entry string
    """
    data = request.get_json() or {}
    url = (data.get('url') or '').strip()
    tracklist_entry_id = data.get('tracklist_entry_id')
    raw_entry = data.get('tracklist_entry') or data.get('full_tracklist_entry')

    if not url:
        return jsonify({'error': 'Missing required field: url'}), 400

    try:
        service_cls = PlatformServiceFactory.get_service_by_url(url)
        if not hasattr(service_cls, 'get_track_by_url'):
            return jsonify({'error': 'Platform does not support URL resolution'}), 400
        track = service_cls.get_track_by_url(url)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error("Error resolving track URL: %s", e, exc_info=True)
        return jsonify({'error': 'Failed to resolve track URL', 'message': str(e)}), 500

    confidence = None
    if tracklist_entry_id or raw_entry:
        try:
            if tracklist_entry_id:
                entry = TracklistEntry.query.get(tracklist_entry_id)
                if not entry:
                    return jsonify({'error': 'Tracklist entry not found'}), 404

                working_entry = TracklistEntry()
                working_entry.full_tracklist_entry = entry.full_tracklist_entry
                working_entry.artist = entry.artist
                working_entry.short_title = entry.short_title
                working_entry.full_title = entry.full_title
                working_entry.version = entry.version
                working_entry.version_artist = entry.version_artist
                working_entry.is_vip = entry.is_vip
                working_entry.unicode_cleaned_entry = entry.unicode_cleaned_entry
                working_entry.prefix_cleaned_entry = entry.prefix_cleaned_entry
                working_entry.is_unidentified = entry.is_unidentified
            else:
                working_entry = TracklistImportService.pre_process_track(raw_entry)

            candidate = SimpleNamespace(
                name=track.get('name') or "",
                artist=track.get('artist') or ""
            )
            feature_scores = FeatureScores(**feature_scoring_utils.calculate_feature_scores_tracks(working_entry, candidate))
            confidence = TracklistPredictionService.predict(feature_scores)
        except Exception as e:
            logger.warning("Failed to calculate confidence for URL track: %s", e)

    return jsonify({'track': track, 'confidence': confidence}), 200


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


@api.route('/api/tracklists/<int:tracklist_id>/download', methods=['POST'])
def download_tracklist(tracklist_id):
    """Download all confirmed tracks in a tracklist that are missing a download location."""
    try:
        tracklist = TracklistRepository.get_tracklist_by_id(tracklist_id)
        if not tracklist:
            return jsonify({'error': 'Tracklist not found'}), 404

        entries = tracklist.tracklist_entries or []
        confirmed_tracks = {}
        to_download = {}

        for entry in entries:
            track = entry.confirmed_track
            if not track:
                continue
            confirmed_tracks[track.id] = track
            if not track.download_location:
                to_download[track.id] = track

        if not to_download:
            return jsonify({
                'tracklist_id': tracklist_id,
                'requested': 0,
                'downloaded': 0,
                'skipped': len(confirmed_tracks),
                'failed': []
            }), 200

        failed = []
        downloaded = 0

        for track in to_download.values():
            try:
                platform = (track.platform or '').lower()
                download_service = DownloadServiceFactory.get_service_by_platform(platform)
                download_service.download_track(track)
                downloaded += 1
            except Exception as e:
                logger.error("Error downloading track %s for tracklist %s: %s", track.id, tracklist_id, e, exc_info=True)
                failed.append({
                    'track_id': track.id,
                    'error': str(e),
                })

        return jsonify({
            'tracklist_id': tracklist_id,
            'requested': len(to_download),
            'downloaded': downloaded,
            'skipped': len(confirmed_tracks) - len(to_download),
            'failed': failed,
        }), 200

    except Exception as e:
        logger.error("Error downloading tracklist: %s", e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to download tracklist', 'message': str(e)}), 500


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
