import logging
import os
import yaml
from flask import Blueprint, request, jsonify, current_app

from app.extensions import db, socketio
from app.models import Track
from app.repositories.playlist_repository import PlaylistRepository
from app.services.export_services.export_itunesxml_service import ExportItunesXMLService
from app.services.playlist_manager_service import PlaylistManagerService
from config import Config
from app.routes import api

logger = logging.getLogger(__name__)


# GET /api/export – trigger export of data and return the export path
@api.route('/api/export', methods=['GET'])
def export_rekordbox():
    logger.info("Exporting Rekordbox XML")
    EXPORT_FOLDER = Config.EXPORT_FOLDER
    EXPORT_FILENAME = 'rekordbox.xml'

    try:
        export_path = ExportItunesXMLService.generate_rekordbox_xml_from_db(EXPORT_FOLDER, EXPORT_FILENAME)
        logger.info("Export successful, location: %s", export_path)
        return jsonify({'export_path': export_path}), 200
    except Exception as e:
        logger.error("Export failed: %s", e)
        return jsonify({'error': 'Export failed', 'message': str(e)}), 500


@api.route('/api/tracks', methods=['GET'])
def get_tracks():
    try:
        tracks = Track.query.all()
        tracks_data = [t.to_dict() for t in tracks]
        return jsonify(tracks_data), 200
    except Exception as e:
        logger.error("Error fetching tracks: %s", e)
        return jsonify({'error': str(e)}), 500


@api.route('/api/playlist/<int:playlist_id>/tracks', methods=['GET'])
def get_playlist_tracks(playlist_id):
    try:
        playlist = PlaylistRepository.get_playlist(playlist_id)
        if not playlist:
            return jsonify({'error': 'Playlist not found'}), 404
        # Return only tracks that exist
        tracks_data = [pt.track.to_dict() for pt in playlist.tracks if pt.track]
        return jsonify(tracks_data), 200
    except Exception as e:
        logger.error("Error fetching tracks for playlist %s: %s", playlist_id, e)
        return jsonify({'error': str(e)}), 500


