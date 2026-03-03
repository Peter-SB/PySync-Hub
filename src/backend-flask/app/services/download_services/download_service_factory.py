import logging
from typing import Type

from app.services.download_services.base_download_service import BaseDownloadService
from app.services.download_services.soundcloud_download_service import SoundcloudDownloadService
from app.services.download_services.spotify_download_service import SpotifyDownloadService
from app.services.download_services.youtube_download_service import YouTubeDownloadService

logger = logging.getLogger(__name__)


class DownloadServiceFactory:
    @staticmethod
    def get_service_by_platform(platform: str) -> Type[BaseDownloadService]:
        """Return the download service class for the given platform."""
        normalized = (platform or "").lower()

        if normalized == "soundcloud":
            return SoundcloudDownloadService
        if normalized == "spotify":
            return SpotifyDownloadService
        if normalized == "youtube":
            return YouTubeDownloadService

        raise ValueError(f"Platform not supported for downloading: {platform}")
