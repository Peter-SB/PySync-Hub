import logging

# For backward compatibility, import SpotifyAPIService as SpotifyService
# This allows existing code that imports SpotifyService to continue working
from app.services.platform_services.spotify_api_service import SpotifyAPIService as SpotifyService

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ['SpotifyService']

# todo: remove SpotifyService alias in future major release