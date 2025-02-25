import logging
import os
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db, socketio
from app.repositories.playlist_repository import PlaylistRepository
from app.services.export_itunesxml_service import ExportItunesXMLService
from app.services.playlist_manager_service import PlaylistManagerService

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)


# GET /api/playlists – returns all playlists in JSON form
@api.route('/api/playlists', methods=['GET'])
def get_playlists():
    try:
        playlists = PlaylistRepository.get_all_playlists()
        # Assuming each Playlist instance has a to_dict() method
        playlists_data = [p.to_dict() for p in playlists]
        return jsonify(playlists_data), 200
    except Exception as e:
        logger.error("Error fetching playlists: %s", e)
        return jsonify({'error': str(e)}), 500


# POST /api/playlists – add a new playlist from a URL or ID
@api.route('/api/playlists', methods=['POST'])
def add_playlist():
    data = request.get_json() or {}
    url_or_id = data.get('url_or_id', '')
    if not url_or_id:
        return jsonify({'error': 'No URL or ID provided'}), 400

    logger.info(f"Adding playlist: {url_or_id}")
    error = PlaylistManagerService.add_playlists(url_or_id)
    if error:
        return jsonify({'error': error}), 400

    # Return updated playlists
    playlists = PlaylistRepository.get_all_playlists()
    playlists_data = [p.to_dict() for p in playlists]
    return jsonify(playlists_data), 201


# POST /api/playlists/refresh – refresh (sync) selected playlists
@api.route('/api/playlists/refresh', methods=['POST'])
def refresh_playlists():
    data = request.get_json() or {}
    selected_ids = data.get('playlist_ids', [])

    # Get playlists by IDs if provided, otherwise all playlists.
    if selected_ids:
        playlists = PlaylistRepository.get_playlists_by_ids(selected_ids)
    else:
        playlists = PlaylistRepository.get_all_playlists()

    # Only refresh active (not disabled) playlists
    playlists = [p for p in playlists if not p.disabled]

    # Set download status and emit update via socketio
    for playlist in playlists:
        playlist.download_status = "queued"
        socketio.emit("download_status", {"id": playlist.id, "status": "queued"})
    db.session.commit()

    # Refresh playlists and queue them for download
    for playlist in playlists:
        PlaylistManagerService.refresh_playlists([playlist])
        current_app.download_manager.add_to_queue(playlist.id)

    updated_playlists = [p.to_dict() for p in playlists]
    return jsonify(updated_playlists), 200


# DELETE /api/playlists – delete selected playlists
@api.route('/api/playlists', methods=['DELETE'])
def delete_playlists():
    data = request.get_json() or {}
    selected_ids = data.get('playlist_ids', [])
    if not selected_ids:
        return jsonify({'error': 'No playlist IDs provided'}), 400

    PlaylistManagerService.delete_playlists(selected_ids)
    playlists = PlaylistRepository.get_all_playlists()
    playlists_data = [p.to_dict() for p in playlists]
    return jsonify(playlists_data), 200


# DELETE /api/download/<playlist_id>/cancel – cancel a download in progress
@api.route("/api/download/<int:playlist_id>/cancel", methods=["DELETE"])
def cancel_download(playlist_id):
    current_app.download_manager.cancel_download(playlist_id)
    playlist = PlaylistRepository.get_playlist(playlist_id)
    if playlist:
        playlist.download_status = 'ready'
        db.session.commit()
        socketio.emit("download_status", {"id": playlist.id, "status": "ready"})
        return jsonify(playlist.to_dict()), 200
    else:
        return jsonify({'error': 'Playlist not found'}), 404


# POST /api/playlists/toggle – toggle the disabled state of a playlist
@api.route('/api/playlists/toggle', methods=['POST'])
def toggle_playlist():
    data = request.get_json() or {}
    playlist_id = data.get('playlist_id')
    disabled_value = data.get('disabled')
    if playlist_id is None or disabled_value is None:
        return jsonify({'error': 'Missing parameters'}), 400

    playlist = PlaylistRepository.get_playlist(playlist_id)
    if not playlist:
        return jsonify({'error': 'Playlist not found'}), 404

    # Convert the value to a boolean
    playlist.disabled = True if str(disabled_value).lower() == 'true' else False
    db.session.commit()
    return jsonify(playlist.to_dict()), 200


# GET /api/export – trigger export of data and return the export path
@api.route('/api/export', methods=['GET'])
def export_rekordbox():
    logger.info("Exporting Rekordbox XML")
    EXPORT_FOLDER = os.path.join(os.getcwd(), 'exports')
    EXPORT_FILENAME = 'rekordbox.xml'

    try:
        export_path = ExportItunesXMLService.generate_rekordbox_xml_from_db(EXPORT_FOLDER, EXPORT_FILENAME)
        logger.info("Export successful, location: %s", export_path)
        return jsonify({'export_path': export_path}), 200
    except Exception as e:
        logger.error("Export failed: %s", e)
        return jsonify({'error': 'Export failed', 'message': str(e)}), 500
