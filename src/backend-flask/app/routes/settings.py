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
        'DOWNLOAD_PATH_PATTERN': 'shared'
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
            'download_path_pattern': settings_data.get('DOWNLOAD_PATH_PATTERN', 'shared'),
            'download_folder': Config.DOWNLOAD_FOLDER
        }), 200

    elif request.method == 'POST':
        data = request.get_json() or {}
        new_settings = {
            'SPOTIFY_CLIENT_ID': data.get('spotify_client_id'),
            'SPOTIFY_CLIENT_SECRET': data.get('spotify_client_secret'),
            'SOUNDCLOUD_CLIENT_ID': data.get('soundcloud_client_id'),
            'DOWNLOAD_PATH_PATTERN': data.get('download_path_pattern', 'shared')
        }
        with open(settings_path, 'w') as f:
            yaml.safe_dump(new_settings, f)

        Config.load_settings()

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
