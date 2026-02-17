import logging
import os
import time

import yaml
from flask import Blueprint, request, jsonify, current_app

from app.extensions import db, socketio
from app.models import Track
from app.routes import api
from app.utils.db_utils import commit_with_retries
from app.services.download_services.download_service_factory import DownloadServiceFactory

logger = logging.getLogger(__name__)

@api.route('/api/tracks', methods=['POST'])
def create_track():
    """Create a new track or return existing track if it already exists."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['platform', 'platform_id', 'name', 'artist']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if track already exists
        track = Track.query.filter_by(
            platform=data['platform'],
            platform_id=data['platform_id'],
        ).first()
        
        # If track doesn't exist, create it
        if not track:
            track = Track(
                platform_id=data['platform_id'],
                platform=data['platform'],
                name=data['name'],
                artist=data['artist'],
                album=data.get('album'),
                album_art_url=data.get('album_art_url'),
                download_url=data.get('download_url')
            )
            db.session.add(track)
            commit_with_retries(db.session)
            logger.info("Created new track: %s - %s (platform: %s)", track.artist, track.name, track.platform)
            return jsonify(track.to_dict()), 201
        else:
            logger.info("Track already exists: %s - %s (id: %s)", track.artist, track.name, track.id)
            return jsonify(track.to_dict()), 200
        
    except Exception as e:
        logger.error("Error creating track: %s", e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to create track', 'message': str(e)}), 500

@api.route('/api/tracks', methods=['GET'])
def get_tracks():
    try:
        tracks = Track.query.all()
        tracks_data = [t.to_dict() for t in tracks]
        return jsonify(tracks_data), 200
    except Exception as e:
        logger.error("Error fetching tracks: %s", e)
        return jsonify({'error': str(e)}), 500

@api.route('/api/tracks/<int:track_id>', methods=['GET'])
def get_track(track_id):
    try:
        logger.info("Fetching track %s", track_id)
        track = Track.query.get(track_id)
        if not track:
            return jsonify({'error': 'Track not found'}), 404

        return jsonify(track.to_dict()), 200
    except Exception as e:
        logger.error("Error fetching track: %s", e, exc_info=True)
        return jsonify({'error': 'Failed to fetch track', 'message': str(e)}), 500

@api.route('/api/tracks/<int:track_id>', methods=['PUT', 'OPTIONS'])
def update_track(track_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200  # Handle preflight request

    try:
        logger.info("Updating track %s", track_id)

        track = Track.query.get(track_id)
        if not track:
            return jsonify({'error': 'Track not found'}), 404

        data = request.get_json() or {}

        if 'download_url' in data:
            track.download_url = data['download_url']
        if 'download_location' in data:
            track.set_download_location(data['download_location'])

        commit_with_retries(db.session)
        return jsonify(track.to_dict()), 200
    except Exception as e:
        logger.error("Error updating track: %s", e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to update track', 'message': str(e)}), 500

@api.route('/api/tracks/<int:track_id>/download', methods=['POST', 'OPTIONS'])
def re_download_track(track_id):
    try:
        logger.info("Re-downloading track %s", track_id)
        track: Track = Track.query.get(track_id)
        if not track:
            return jsonify({'error': 'Track not found'}), 404

        # Get the absolute path for file operations
        absolute_path = track.absolute_download_path
        logger.info("Clearing previous download for track %s, location %s", track_id, absolute_path)
        
        if absolute_path and os.path.exists(absolute_path):
            logger.info("Removing file, location %s", absolute_path)
            os.remove(absolute_path)

        # Optionally clear previous download details
        track.download_location = None
        track.notes_errors = ""
        db.session.commit()

        # Determine which download service to use based on platform
        # download_service = DownloadServiceFactory.get_service_by_platform(track.platform)
        # download_service.download_track(track)

        if track.platform.lower() == "spotify":
            from app.services.download_services.spotify_download_service import SpotifyDownloadService
            SpotifyDownloadService.download_track(track)
        elif track.platform.lower() == "soundcloud":
            from app.services.download_services.soundcloud_download_service import SoundcloudDownloadService
            SoundcloudDownloadService.download_track(track)
        elif track.platform.lower() == "youtube":
            from app.services.download_services.youtube_download_service import YouTubeDownloadService
            YouTubeDownloadService.download_track(track)

        else:
            return jsonify({'error': 'Platform not supported for downloading'}), 400
        logger.info("Re-downloaded track %s", Track.query.get(track_id).to_dict())
        return jsonify(Track.query.get(track_id).to_dict()), 200

    except Exception as e:
        logger.error("Error re-downloading track (ID: %s): %s", track_id, e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to re-download track', 'message': str(e)}), 500
