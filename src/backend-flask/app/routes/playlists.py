import logging
import os
from datetime import datetime

import yaml
from flask import Blueprint, request, jsonify, current_app

from app.extensions import db, socketio
from app.models import Track, Playlist
from app.repositories.folder_repository import FolderRepository
from app.repositories.playlist_repository import PlaylistRepository
from app.repositories.track_repository import TrackRepository
from app.services.export_services.export_itunesxml_service import ExportItunesXMLService
from app.services.playlist_manager_service import PlaylistManagerService
from config import Config
from app.routes import api
from app.utils.db_utils import commit_with_retries
from app.services.platform_services.soundcloud_service import SoundCloudAuthError


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
        # Return only tracks with added date
        tracks_data = [
            {**pt.track.to_dict(), "added_on": pt.added_on.isoformat() if pt.added_on else None}
            for pt in playlist.tracks if pt.track
        ]
        return jsonify(tracks_data), 200
    except Exception as e:
        logger.error("Error fetching tracks for playlist %s: %s", playlist_id, e)
        return jsonify({'error': str(e)}), 500


@api.route('/api/playlists', methods=['POST'])
def add_playlist():
    data = request.get_json() or {}
    url_or_id = data.get('url_or_id', '')
    date_limit = data.get('date_limit', None)
    track_limit = data.get('track_limit', None)
    if not url_or_id:
        return jsonify({'error': 'No URL or ID provided'}), 400

    logger.info(f"Adding playlist: {url_or_id}")
    error = PlaylistManagerService.add_playlists(url_or_id, date_limit, track_limit)
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
    quick_sync = data.get('quick_sync', True)

    try:
        # Get playlists in custom order and filter by selected IDs if provided.
        playlists = FolderRepository.get_playlists_in_custom_order()
        if selected_ids:
            playlists = [playlist for playlist in playlists if playlist.id in selected_ids]

        # Set download status and emit update via socketio
        for playlist in playlists:
            playlist.download_status = "queued"
            socketio.emit("download_status", {"id": playlist.id, "status": "queued"})
        commit_with_retries(db.session)

        # Sync playlists and queue them for download
        for playlist in playlists:
            try:
                PlaylistManagerService.sync_playlists([playlist])
            except Exception as e:
                # Check for SoundCloudAuthError
                if isinstance(e, SoundCloudAuthError):
                    return jsonify({'error': 'Authentication Error. Please refresh your SoundCloud token in Settings.'}), 401
                raise
            current_app.download_manager.add_to_queue(playlist.id, quick_sync)

        updated_playlists = [p.to_dict() for p in playlists]
        return jsonify(updated_playlists), 200
    except Exception as e:
        logger.error("Error syncing playlists: %s", e, exc_info=True)
        return jsonify({'error': str(e)}), 500


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


@api.route('/api/playlists/<int:playlist_id>', methods=['DELETE'])
def delete_single_playlist(playlist_id):
    PlaylistManagerService.delete_playlists([playlist_id])
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
    commit_with_retries(db.session)

    # After toggling the playlist, recursively update parent folders' disabled states
    if playlist.folder_id:
        folder_id = playlist.folder_id
        # Update the immediate parent folder first
        FolderRepository.update_folder_disabled_state(folder_id)
        
        # Then recursively check all ancestors
        current_folder = FolderRepository.get_folder_by_id(folder_id)
        while current_folder and current_folder.parent_id:
            FolderRepository.update_folder_disabled_state(current_folder.parent_id)
            current_folder = FolderRepository.get_folder_by_id(current_folder.parent_id)
    
    return jsonify(playlist.to_dict()), 200


@api.route('/api/playlists/toggle-multiple', methods=['POST'])
def toggle_multiple_playlists():
    data = request.get_json() or {}
    playlist_ids = data.get('playlist_ids', [])
    disabled_value = data.get('disabled')
    
    if not playlist_ids or disabled_value is None:
        return jsonify({'error': 'Missing parameters'}), 400

    # Convert the disabled value to a boolean
    disabled = True if str(disabled_value).lower() == 'true' else False
    
    try:
        # Get all playlists by IDs
        playlists = PlaylistRepository.get_playlists_by_ids(playlist_ids)
        updated_playlists = []
        
        # Keep track of affected folder IDs for later updates
        affected_folder_ids = set()
        
        # Update each playlist's disabled status
        for playlist in playlists:
            playlist.disabled = disabled
            updated_playlists.append(playlist.to_dict())
            
            # Add the folder ID to the affected set if the playlist is in a folder
            if playlist.folder_id:
                affected_folder_ids.add(playlist.folder_id)

        commit_with_retries(db.session)

        # Update all affected folders and their ancestors
        for folder_id in affected_folder_ids:
            # Update the immediate parent folder first
            FolderRepository.update_folder_disabled_state(folder_id)
            
            # Then recursively check all ancestors
            current_folder = FolderRepository.get_folder_by_id(folder_id)
            while current_folder and current_folder.parent_id:
                FolderRepository.update_folder_disabled_state(current_folder.parent_id)
                current_folder = FolderRepository.get_folder_by_id(current_folder.parent_id)
        
        return jsonify(updated_playlists), 200
    except Exception as e:
        logger.error(f"Error toggling multiple playlists: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to toggle playlists'}), 500


@api.route('/api/playlists/<int:playlist_id>', methods=['PATCH'])
def update_playlist(playlist_id):
    data = request.get_json() or {}

    playlist = PlaylistRepository.get_playlist(playlist_id)
    if not playlist:
        return jsonify({'error': 'Playlist not found'}), 404

    # Update date_limit if provided
    if 'date_limit' in data and data['date_limit']:
        try:
            playlist.date_limit = datetime.strptime(data['date_limit'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
        TrackRepository.remove_tracks_before_date(playlist, playlist.date_limit)
    else:
        playlist.date_limit = None

    # Update track_limit if provided
    if 'track_limit' in data and data['track_limit']:
        try:
            logger.info("Updating track limit to %s", int(data['track_limit']))
            playlist.track_limit = int(data['track_limit'])
        except ValueError:
            logger.error("Invalid track limit: %s", data['track_limit'])
            return jsonify({'error': 'Invalid track. Must be an integer.'}), 400
        TrackRepository.remove_excess_tracks(playlist, playlist.track_limit)
    else:
        playlist.track_limit = None

    commit_with_retries(db.session)

    return jsonify(playlist.to_dict()), 200


@api.route('/api/playlists/<int:playlist_id>/refresh', methods=['POST'])
def refresh_playlist(playlist_id):
    try:
        playlist = PlaylistRepository.get_playlist(playlist_id)
        if not playlist:
            return jsonify({'error': 'Playlist not found'}), 404

        # Sync playlist info and tracks without downloading
        PlaylistManagerService.sync_playlists([playlist])

        return jsonify(playlist.to_dict()), 200
    except Exception as e:
        logger.error("Error refreshing playlist %s: %s", playlist_id, e)
        return jsonify({'error': str(e)}), 500


@api.route('/api/playlists/move', methods=['POST'])
def move_playlist():
    """Move a playlist to a different folder and/or position."""
    try:
        data = request.json
        playlist_id = data.get('id')
        new_folder_id = data.get('parent_id')  # can be None (root level)
        position = data.get('position', 0)

        playlist = PlaylistRepository.get_playlist(playlist_id)
        if not playlist:
            return jsonify({'error': 'Playlist not found'}), 404
        
        # If folder specified, verify it exists
        if new_folder_id is not None:
            folder = FolderRepository.get_folder_by_id(new_folder_id)
            if not folder:
                return jsonify({'error': 'Folder not found'}), 404

        # Get all sibling playlists at the target level
        siblings = db.session.query(Playlist).filter_by(
            folder_id=new_folder_id
        ).order_by(Playlist.custom_order).all()

        # Remove the playlist from its current position if it's among the siblings
        if playlist.folder_id == new_folder_id:
            siblings = [s for s in siblings if s.id != playlist_id]

        # Insert the playlist at the specified position
        siblings.insert(min(position, len(siblings)), playlist)
        
        # Update custom_order for all siblings
        for i, sibling in enumerate(siblings):
            sibling.custom_order = i
            db.session.add(sibling)
        
        # Update the folder_id
        playlist.folder_id = new_folder_id
        
        commit_with_retries(db.session)
        
        return jsonify({
            'message': 'Playlist moved successfully',
            'playlist': playlist.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error moving playlist: {str(e)}")
        return jsonify({'error': 'Failed to move playlist'}), 500
