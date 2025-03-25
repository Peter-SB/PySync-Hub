import logging

from app.services.platform_services.soundcloud_service import SoundcloudService
from app.services.platform_services.spotify_service import SpotifyService

logger = logging.getLogger(__name__)

class MusicPlatformFactory:
    @staticmethod
    def get_service(url_or_id):
        """Returns the appropriate service instance based on the URL."""
        if "soundcloud.com" in url_or_id:
            return SoundcloudService
        else:
            return SpotifyService