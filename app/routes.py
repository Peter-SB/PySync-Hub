import logging

from flask import Blueprint, render_template, request
from app.models import Playlist
from app.services.spotify import SpotifyService
from app import db
from datetime import datetime

logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)


@main.route('/')
def index():
    logger.info("Index page requested")
    return render_template('index.html')


@main.route('/playlists')
def get_playlists():
    selected_ids = request.args.getlist('selected_ids')
    logger.info(f"Retrieving playlists. Selected IDs from query params: %s", selected_ids)
    playlists = Playlist.query.order_by(Playlist.created_at.desc()).all()
    logger.info(f"Playlists: {[playlist.to_dict() for playlist in playlists]}")
    return render_template('partials/playlist_list.html',
                           playlists=playlists,
                           selected_ids=selected_ids)


@main.route('/playlists', methods=['POST'])
def add_playlist():
    url_or_id = request.form.get('url_or_id')
    logger.info("Attempting to add playlist with url_or_id: %s", url_or_id)
    service = 'spotify'  # Will be extended for SoundCloud

    try:
        playlist_data = SpotifyService.get_playlist_data(url_or_id)
        logger.debug("Fetched playlist data: %s", playlist_data)

        existing = Playlist.query.filter_by(
            external_id=playlist_data['external_id'],
            service=service
        ).first()

        if existing:
            logger.info("Playlist already exists with external_id: %s", playlist_data['external_id'])
        else:
            playlist = Playlist(
                name=playlist_data['name'],
                service=service,
                external_id=playlist_data['external_id'],
                image_url=playlist_data['image_url'],
                track_count=playlist_data['track_count']
            )
            db.session.add(playlist)
            db.session.commit()
            logger.info("Added new playlist with external_id: %s", playlist_data['external_id'])

    except Exception as e:
        logger.error("Error adding playlist with url_or_id '%s': %s", url_or_id, e, exc_info=True)
        # Optionally, handle the error further (e.g., flash a message or return an error response)

    return get_playlists()

@main.route('/playlists/sync', methods=['POST'])
def sync_playlists():
    selected_ids = request.form.getlist('playlist_ids')
    logger.info("Syncing playlists. Selected IDs: %s", selected_ids)

    if selected_ids:
        try:
            selected_ids_int = [int(pid) for pid in selected_ids]
        except ValueError as ve:
            logger.error("Invalid playlist ID format in selected_ids: %s", selected_ids)
            selected_ids_int = []
        playlists = Playlist.query.filter(Playlist.id.in_(selected_ids_int)).all()
    else:
        playlists = Playlist.query.all()

    for playlist in playlists:
        if playlist.service == 'spotify':
            try:
                data = SpotifyService.get_playlist_data(playlist.external_id)
                playlist.name = data['name']
                playlist.last_synced = datetime.utcnow()
                playlist.image_url = data["image_url"]
                playlist.track_count = data["track_count"]
                logger.info("Synced playlist (ID: %s, external_id: %s)", playlist.id, playlist.external_id)
            except Exception as e:
                logger.error("Failed to sync playlist ID %s: %s", playlist.id, e, exc_info=True)

    try:
        db.session.commit()
        logger.info("Database commit successful after syncing playlists")
    except Exception as e:
        logger.error("Database commit failed during sync: %s", e, exc_info=True)

    return get_playlists()


@main.route('/playlists', methods=['DELETE'])
def delete_playlists():
    selected_ids = request.form.getlist('playlist_ids')
    logger.info("Deleting playlists with IDs: %s", selected_ids)

    if selected_ids:
        try:
            selected_ids_int = [int(pid) for pid in selected_ids]
        except ValueError as ve:
            logger.error("Invalid playlist ID format in selected_ids: %s", selected_ids)
            selected_ids_int = []

        try:
            # Bulk delete; synchronize_session=False for performance since we don't need the session updates
            Playlist.query.filter(Playlist.id.in_(selected_ids_int)).delete(synchronize_session=False)
            db.session.commit()
            logger.info("Deleted playlists with IDs: %s", selected_ids_int)
        except Exception as e:
            logger.error("Error deleting playlists with IDs %s: %s", selected_ids_int, e, exc_info=True)

    return get_playlists()