import logging
from typing import Type
from urllib.parse import urlparse

from app.services.platform_services.base_platform_service import BasePlatformService
from app.services.platform_services.soundcloud_service import SoundcloudService
from app.services.platform_services.spotify_api_service import SpotifyApiService
from app.services.platform_services.spotify_scraper_service import SpotifyScraperService
from app.services.platform_services.youtube_service import YouTubeService
from config import Config

logger = logging.getLogger(__name__)


class PlatformServiceFactory:
    @staticmethod
    def _has_spotify_credentials() -> bool:
        """Check if Spotify API credentials are configured."""
        return bool(
            Config.SPOTIFY_CLIENT_ID 
            and Config.SPOTIFY_CLIENT_SECRET 
            and Config.SPOTIFY_CLIENT_ID.strip() 
            and Config.SPOTIFY_CLIENT_SECRET.strip()
        )

    @staticmethod
    def _get_spotify_service() -> Type[SpotifyApiService | SpotifyScraperService]:
        """
        Returns the appropriate Spotify service based on credential availability.
        Falls back to SpotifyScraperService if no API credentials are configured.
        """
        if PlatformServiceFactory._has_spotify_credentials():
            logger.info("Using Spotify API Service (credentials found)")
            return SpotifyApiService
        else:
            logger.info("Using Spotify Scraper Service (no credentials found)")
            return SpotifyScraperService

    @staticmethod
    def get_service_by_platform(platform: str) -> Type[BasePlatformService]:
        """Returns the appropriate service instance based on the platform."""
        if platform == "soundcloud":
            return SoundcloudService
        elif platform == "spotify":
            return PlatformServiceFactory._get_spotify_service()
        elif platform == "youtube":
            return YouTubeService
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    @staticmethod
    def get_service_by_url(url: str) -> Type[BasePlatformService]:
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
                return PlatformServiceFactory._get_spotify_service()
            elif trusted_youtube:
                return YouTubeService
            else:
                raise ValueError(f"URL Doesn't Look Right. Please try again with a valid URL.")
        except ValueError:
            raise
        except Exception as e:
            logger.error("Error parsing URL: %s", e)
            raise ValueError(f"URL Doesn't Look Right. Please try again with a valid URL.")
