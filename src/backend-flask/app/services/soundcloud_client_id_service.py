import logging
import os
import re

import requests
import yaml


logger = logging.getLogger(__name__)

SOUNDCLOUD_HOMEPAGE_URL = "https://soundcloud.com/"
SOUNDCLOUD_CLIENT_ID_PATTERN = re.compile(
    r'\{"hydratable"\s*:\s*"apiClient"\s*,\s*"data"\s*:\s*\{\s*"id"\s*:\s*"([^"]+)"'
)
DEFAULT_SETTINGS = {
    "SPOTIFY_CLIENT_ID": "",
    "SPOTIFY_CLIENT_SECRET": "",
    "SOUNDCLOUD_CLIENT_ID": "",
}

SOUNDCLOUD_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def fetch_soundcloud_client_id(timeout: int = 10) -> str:
    """Fetch the latest SoundCloud client_id from SoundCloud homepage hydration data."""
    response = requests.get(SOUNDCLOUD_HOMEPAGE_URL, headers=SOUNDCLOUD_HEADERS, timeout=timeout)
    response.raise_for_status()

    match = SOUNDCLOUD_CLIENT_ID_PATTERN.search(response.text)
    if not match:
        raise ValueError("Failed to extract client_id from SoundCloud homepage")

    return match.group(1)


def refresh_soundcloud_client_id(config_class, persist: bool = True, timeout: int = 10) -> str:
    """
    Fetch and apply latest SoundCloud client_id.
    Optionally persists to settings.yml and updates config class in-memory value.
    """
    client_id = fetch_soundcloud_client_id(timeout=timeout)

    if persist:
        settings_path = config_class.SETTINGS_PATH
        settings_dir = os.path.dirname(settings_path)
        if settings_dir:
            os.makedirs(settings_dir, exist_ok=True)

        settings_data = dict(DEFAULT_SETTINGS)
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as stream:
                loaded_settings = yaml.safe_load(stream) or {}
            if isinstance(loaded_settings, dict):
                settings_data.update(loaded_settings)

        settings_data["SOUNDCLOUD_CLIENT_ID"] = client_id
        with open(settings_path, "w", encoding="utf-8") as stream:
            yaml.safe_dump(settings_data, stream, default_flow_style=False)

    config_class.SOUNDCLOUD_CLIENT_ID = client_id
    logger.info("SoundCloud client_id refreshed successfully")
    return client_id
