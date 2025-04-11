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

    try:
        export_path = ExportItunesXMLService.generate_rekordbox_xml_from_db(Config.EXPORT_FOLDER, Config.EXPORT_FILENAME)
        logger.info("Export successful, location: %s", export_path)
        return jsonify({'export_path': os.path.normpath(export_path)}), 200
    except Exception as e:
        logger.error("Export failed: %s", e)
        return jsonify({'error': 'Export failed', 'message': str(e)}), 500
