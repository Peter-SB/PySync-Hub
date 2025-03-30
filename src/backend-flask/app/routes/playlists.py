import logging
import os
from datetime import datetime

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

@api.route('/api/playlists', methods=['GET'])
def get_playlists():
    try:
        playlists = PlaylistRepository.get_all_playlists()
        playlists_data = [p.to_dict() for p in playlists]

        return jsonify(playlists_data), 200
    except Exception as e:
        logger.error("Error fetching playlists: %s", e)
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


@api.route('/api/playlists/sync', methods=['POST'])
def sync_playlists():
    data = request.get_json() or {}
    selected_ids = data.get('playlist_ids', [])

    # Get playlists by IDs if provided, otherwise all playlists.
    if selected_ids:
        playlists = PlaylistRepository.get_playlists_by_ids(selected_ids)
    else:
        playlists = PlaylistRepository.get_all_playlists()

    # Only sync active (not disabled) playlists
    playlists = [p for p in playlists if not p.disabled]

    # Set download status and emit update via socketio
    for playlist in playlists:
        playlist.download_status = "queued"
        socketio.emit("download_status", {"id": playlist.id, "status": "queued"})
    db.session.commit()

    # Sync playlists and queue them for download
    for playlist in playlists:
        PlaylistManagerService.sync_playlists([playlist])
        current_app.download_manager.add_to_queue(playlist.id)

    updated_playlists = [p.to_dict() for p in playlists]
    return jsonify(updated_playlists), 200


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


@api.route("/api/download/<int:playlist_id>/cancel", methods=["DELETE"])
def cancel_download(playlist_id):
    current_app.download_manager.cancel_download(playlist_id)
    playlist = PlaylistRepository.get_playlist(playlist_id)
    if playlist:
        PlaylistRepository.set_download_status(playlist, "ready")
        return jsonify(playlist.to_dict()), 200
    else:
        return jsonify({'error': 'Playlist not found'}), 404


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


@api.route('/api/playlists/<int:playlist_id>', methods=['PATCH'])
def update_playlist(playlist_id):
    data = request.get_json() or {}
    
    playlist = PlaylistRepository.get_playlist(playlist_id)
    if not playlist:
        return jsonify({'error': 'Playlist not found'}), 404

    # Update date_limit if provided
    if 'date_limit' in data and data['date_limit']:
        try:
            playlist.date_limit = datetime.strptime(data['date_limit'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400


    # Update track_limit if provided
    if 'track_limit' in data and data['track_limit']:
        playlist.track_limit = data['track_limit']

    try:
        db.session.commit()
        return jsonify(playlist.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Error updating playlist %s: %s", playlist_id, e)
        return jsonify({'error': str(e)}), 500


