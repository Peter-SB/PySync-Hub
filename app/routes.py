import logging
import os
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db, socketio
from app.models import Track
from app.repositories.playlist_repository import PlaylistRepository
from app.services.export_services.export_itunesxml_service import ExportItunesXMLService
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


@api.route('/api/settings', methods=['GET', 'POST'])
def settings():
    import os
    from flask import current_app, request, jsonify

    env_path = os.path.join(current_app.root_path, '..', '.env')

    def read_env_file():
        env_data = {}
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
            for line in lines:
                if '=' in line and not line.startswith('#'):
                    key, val = line.strip().split('=', 1)
                    env_data[key] = val
        return env_data, lines

    if request.method == 'GET':
        env_data, _ = read_env_file()
        return jsonify({
            'spotify_client_id': env_data.get('SPOTIFY_CLIENT_ID', ''),
            'spotify_client_secret': env_data.get('SPOTIFY_CLIENT_SECRET', ''),
            'soundcloud_client_id': env_data.get('SOUNDCLOUD_CLIENT_ID', '')
        }), 200

    elif request.method == 'POST':
        data = request.get_json() or {}
        spotify_client_id = data.get('spotify_client_id')
        spotify_client_secret = data.get('spotify_client_secret')
        soundcloud_client_id = data.get('soundcloud_client_id')

        # All three fields must be provided.
        # if spotify_client_id is None or spotify_client_secret is None or soundcloud_client_id is None:
        #     return jsonify({'error': 'Missing one or more required settings'}), 400

        env_data, lines = read_env_file()
        # Keys to update
        keys_to_update = {
            'SPOTIFY_CLIENT_ID': spotify_client_id,
            'SPOTIFY_CLIENT_SECRET': spotify_client_secret,
            'SOUNDCLOUD_CLIENT_ID': soundcloud_client_id
        }
        new_lines = []
        keys_updated = set()

        for line in lines:
            if '=' in line and not line.startswith('#'):
                key, _ = line.strip().split('=', 1)
                if key in keys_to_update:
                    new_lines.append(f"{key}={keys_to_update[key]}\n")
                    keys_updated.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # Add keys that weren't present
        for key, val in keys_to_update.items():
            if key not in keys_updated:
                new_lines.append(f"{key}={val}\n")

        try:
            with open(env_path, 'w') as f:
                f.writelines(new_lines)
            return jsonify({'message': 'Settings updated successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

