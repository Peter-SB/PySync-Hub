import logging
import os
import re
import yaml
from flask import request, jsonify, session, redirect, url_for
from spotipy import SpotifyOAuth
import requests

from config import Config
from app.routes import api
from app.services.platform_services.spotify_api_service import SpotifyApiService

logger = logging.getLogger(__name__)


@api.route('/api/settings', methods=['GET', 'POST'])
def settings():
    DEFAULT_SETTINGS = {
        'SPOTIFY_CLIENT_ID': '',
        'SPOTIFY_CLIENT_SECRET': '',
        'SOUNDCLOUD_CLIENT_ID': ''
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
            'soundcloud_client_id': settings_data.get('SOUNDCLOUD_CLIENT_ID', '')
        }), 200

    elif request.method == 'POST':
        data = request.get_json() or {}
        new_settings = {
            'SPOTIFY_CLIENT_ID': data.get('spotify_client_id'),
            'SPOTIFY_CLIENT_SECRET': data.get('spotify_client_secret'),
            'SOUNDCLOUD_CLIENT_ID': data.get('soundcloud_client_id')
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
    auth_client = SpotifyApiService.get_auth_client(Config.SPOTIFY_REDIRECT_URI).auth_manager
    auth_url = auth_client.get_authorize_url()
    logger.info("Logging in to Spotify")
    return redirect(auth_url)


@api.route('/api/spotify_auth/logout')
def spotify_logout():
    auth_client = SpotifyApiService.get_auth_client().auth_manager
    auth_client.cache_handler.delete_cached_token()
    logger.info("Logging out of Spotify")
    return jsonify({'message': 'Logged out of Spotify'}), 200


@api.route('/api/soundcloud/fetch_client_id', methods=['GET'])
def fetch_soundcloud_client_id():
    """
    Fetches the SoundCloud client_id by scraping the SoundCloud homepage.
    The client_id is embedded in the page's hydration data.
    """
    try:
        logger.info("Fetching SoundCloud client_id from homepage")
        
        # Make request to SoundCloud homepage
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        response = requests.get('https://soundcloud.com/', headers=headers, timeout=10)
        response.raise_for_status()
        
        html_content = response.text
        
        # Look for the apiClient data in the page
        # Pattern: {"hydratable": "apiClient", "data": { "id": "...", ...
        pattern = r'\{"hydratable"\s*:\s*"apiClient"\s*,\s*"data"\s*:\s*\{\s*"id"\s*:\s*"([^"]+)"'
        match = re.search(pattern, html_content)
        
        if match:
            client_id = match.group(1)
            logger.info("Successfully fetched SoundCloud client_id: %s", client_id)
            return jsonify({
                'client_id': client_id,
                'message': 'SoundCloud client_id fetched successfully'
            }), 200
        else:
            logger.error("Failed to find SoundCloud client_id in page content")
            return jsonify({
                'error': 'Failed to extract client_id from SoundCloud homepage'
            }), 500
            
    except requests.RequestException as e:
        logger.error("Error fetching SoundCloud homepage: %s", e)
        return jsonify({
            'error': f'Failed to fetch SoundCloud homepage: {str(e)}'
        }), 500
    except Exception as e:
        logger.error("Unexpected error fetching SoundCloud client_id: %s", e)
        return jsonify({
            'error': f'Unexpected error: {str(e)}'
        }), 500
