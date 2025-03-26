import logging

from app.services.platform_services.soundcloud_service import SoundcloudService
from app.services.platform_services.spotify_service import SpotifyService

logger = logging.getLogger(__name__)


class MusicPlatformFactory:
    @staticmethod
    def get_service(platform):
        """Returns the appropriate service instance based on the platform."""
        if platform == "soundcloud":
            return SoundcloudService
        elif platform == "spotify":
            return SpotifyService
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    @staticmethod
    def get_service_by_url(url):
        """Returns the appropriate service instance based on the URL."""
        if "soundcloud.com" in url:
            return SoundcloudService
        elif "spotify.com" in url:
            return SpotifyService
        else:
            raise ValueError(f"URL Doesnt Look Right. Please try again with a valid URL.")
