import logging
import os
import yaml
from flask import request, jsonify, session, redirect, url_for
from spotipy import SpotifyOAuth

from app import SpotifyService
from config import Config
from app.routes import api

logger = logging.getLogger(__name__)


@api.route('/api/settings', methods=['GET', 'POST'])
def settings():
    DEFAULT_SETTINGS = {
        'SPOTIFY_CLIENT_ID': '',
        'SPOTIFY_CLIENT_SECRET': '',
        'SOUNDCLOUD_CLIENT_ID': '',
        'ENABLE_SPOTIFY_RECENTLY_PLAYED': False
    }
    logger.info("Settings endpoint hit")

    settings_path = Config.SETTINGS_PATH

    if not os.path.exists(settings_path):
        logger.info("Creating default settings file at location:%s", settings_path)
        with open(settings_path, 'w') as f:
            yaml.safe_dump(DEFAULT_SETTINGS, f)

    if request.method == 'GET':
        logger.info("Loading settings file at location:%s", settings_path)
        with open(settings_path, 'r') as f:
            settings_data = yaml.safe_load(f)
        return jsonify({
            'spotify_client_id': settings_data.get('SPOTIFY_CLIENT_ID', ''),
            'spotify_client_secret': settings_data.get('SPOTIFY_CLIENT_SECRET', ''),
            'soundcloud_client_id': settings_data.get('SOUNDCLOUD_CLIENT_ID', ''),
            'enable_spotify_recently_played': settings_data.get('ENABLE_SPOTIFY_RECENTLY_PLAYED', False)
        }), 200

    elif request.method == 'POST':
        from app.models import Playlist
        from app.repositories.playlist_repository import PlaylistRepository
        from app.services.playlist_manager_service import PlaylistManagerService
        
        data = request.get_json() or {}
        new_settings = {
            'SPOTIFY_CLIENT_ID': data.get('spotify_client_id'),
            'SPOTIFY_CLIENT_SECRET': data.get('spotify_client_secret'),
            'SOUNDCLOUD_CLIENT_ID': data.get('soundcloud_client_id'),
            'ENABLE_SPOTIFY_RECENTLY_PLAYED': data.get('enable_spotify_recently_played', False)
        }
        
        # Get old setting value by reading from file to avoid race conditions
        with open(settings_path, 'r') as f:
            old_settings = yaml.safe_load(f)
        old_enable_recently_played = old_settings.get('ENABLE_SPOTIFY_RECENTLY_PLAYED', False)
        new_enable_recently_played = new_settings['ENABLE_SPOTIFY_RECENTLY_PLAYED']
        
        with open(settings_path, 'w') as f:
            yaml.safe_dump(new_settings, f)

        Config.load_settings()
        
        # Handle recently played playlist based on toggle
        if new_enable_recently_played and not old_enable_recently_played:
            # Toggle turned ON - add the playlist
            existing = Playlist.query.filter_by(
                external_id="recently-played",
                platform="spotify"
            ).first()
            
            if not existing:
                logger.info("Adding recently played playlist")
                error = PlaylistManagerService.add_playlists("https://open.spotify.com/recently-played")
                if error:
                    logger.error("Failed to add recently played playlist: %s", error)
        elif not new_enable_recently_played and old_enable_recently_played:
            # Toggle turned OFF - remove the playlist
            existing = Playlist.query.filter_by(
                external_id="recently-played",
                platform="spotify"
            ).first()
            
            if existing:
                logger.info("Removing recently played playlist")
                try:
                    PlaylistManagerService.delete_playlists([existing.id])
                except Exception as e:
                    logger.error("Failed to delete recently played playlist: %s", e)

        return jsonify({'message': 'Settings updated successfully'}), 200


@api.route('/api/spotify_auth/callback')
def spotify_callback():
    """
    OAuth callback endpoint that Spotify redirects to after user authentication.
    It exchanges the authorization code for an access token and stores it in the session.
    """
    auth_manager = SpotifyOAuth(
        client_id=Config.SPOTIFY_CLIENT_ID,
        client_secret=Config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=Config.SPOTIFY_REDIRECT_URI,
        scope=Config.SPOTIFY_OAUTH_SCOPE
    )
    code = request.args.get('code')
    if not code:
        return "Error: no code provided"

    token_info = auth_manager.get_access_token(code)
    session['token_info'] = token_info
    logger.info("Spotify authentication successful; token info stored in session.")

    return jsonify(
        {'message': 'Spotify Login Successful'}), 200  # todo: redirect to frontend or something nicer than this


@api.route('/api/spotify_auth/login')
def spotify_login():
    auth_client = SpotifyService.get_auth_client(Config.SPOTIFY_REDIRECT_URI).auth_manager
    auth_url = auth_client.get_authorize_url()
    logger.info("Logging in to Spotify")
    return redirect(auth_url)


@api.route('/api/spotify_auth/logout')
def spotify_logout():
    auth_client = SpotifyService.get_auth_client().auth_manager
    auth_client.cache_handler.delete_cached_token()
    logger.info("Logging out of Spotify")
    return jsonify({'message': 'Logged out of Spotify'}), 200
