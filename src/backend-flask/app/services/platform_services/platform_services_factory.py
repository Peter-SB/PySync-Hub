import logging
from typing import Type
from urllib.parse import urlparse

from app.services.platform_services.soundcloud_service import SoundcloudService
from app.services.platform_services.spotify_service import SpotifyService
from app.services.platform_services.youtube_service import YouTubeService

logger = logging.getLogger(__name__)


class PlatformServiceFactory:
    @staticmethod
    def get_service(platform: str) -> Type[SoundcloudService | SpotifyService | YouTubeService]:
        """Returns the appropriate service instance based on the platform."""
        if platform == "soundcloud":
            return SoundcloudService
        elif platform == "spotify":
            return SpotifyService
        elif platform == "youtube":
            return YouTubeService
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    @staticmethod
    def get_service_by_url(url: str) -> Type[SoundcloudService | SpotifyService | YouTubeService]:
        """
        Returns the appropriate service instance based on the URL.
        Uses proper URL parsing to avoid substring sanitization vulnerabilities.
        """
        try:
            parsed = urlparse(url)
            hostname = (parsed.hostname or "").lower()
            
            trusted_soundcloud = hostname == "soundcloud.com" or hostname.endswith(".soundcloud.com")
            trusted_spotify = hostname == "spotify.com" or hostname.endswith(".spotify.com")
            trusted_youtube = (
                hostname == "youtube.com" or hostname.endswith(".youtube.com") or
                hostname == "youtu.be" or hostname.endswith(".youtu.be")
            )
            
            if trusted_soundcloud:
                return SoundcloudService
            elif trusted_spotify:
                return SpotifyService
            elif trusted_youtube:
                return YouTubeService
            else:
                raise ValueError(f"URL Doesn't Look Right. Please try again with a valid URL.")
        except ValueError:
            raise
        except Exception as e:
            logger.error("Error parsing URL: %s", e)
            raise ValueError(f"URL Doesn't Look Right. Please try again with a valid URL.")
