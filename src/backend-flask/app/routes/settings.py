import logging
import os
import yaml
from flask import request, jsonify

from config import Config
from app.routes import api

logger = logging.getLogger(__name__)

@api.route('/api/settings', methods=['GET'])
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


