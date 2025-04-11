import logging
import os
import time

import yaml
from flask import Blueprint, request, jsonify, current_app

from app.extensions import db, socketio
from app.models import Track
from app.repositories.playlist_repository import PlaylistRepository
from app.routes import api
from app.services.export_services.export_itunesxml_service import ExportItunesXMLService
from app.services.playlist_manager_service import PlaylistManagerService
from config import Config

logger = logging.getLogger(__name__)

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
            track.download_location = data['download_location']

        db.session.commit()
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

        logger.info("Clearing previous download for track %s, location %s", track_id, track.download_location)
        if track.download_location and os.path.exists(track.download_location):
            logger.info("Removing file, location %s", track.download_location)
            os.remove(track.download_location)

        # Optionally clear previous download details
        track.download_location = None
        track.notes_errors = ""
        db.session.commit()

        # Determine which download service to use based on platform
        if track.platform.lower() == "spotify":
            from app.services.download_services.spotify_download_service import SpotifyDownloadService
            SpotifyDownloadService.download_track(track)
        elif track.platform.lower() == "soundcloud":
            from app.services.download_services.soundcloud_download_service import SoundcloudDownloadService
            SoundcloudDownloadService.download_track(track)
        else:
            return jsonify({'error': 'Platform not supported for downloading'}), 400
        logger.info("Re-downloaded track %s", Track.query.get(track_id).to_dict())
        return jsonify(Track.query.get(track_id).to_dict()), 200

    except Exception as e:
        logger.error("Error re-downloading track (ID: %s): %s", track_id, e, exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Failed to re-download track', 'message': str(e)}), 500
