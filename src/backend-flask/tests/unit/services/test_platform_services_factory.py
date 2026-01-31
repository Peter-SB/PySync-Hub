"""Unit tests for PlatformServiceFactory."""
import pytest
import importlib

from app.services.platform_services.soundcloud_service import SoundcloudService
from app.services.platform_services.spotify_api_service import SpotifyApiService
from app.services.platform_services.spotify_scraper_service import SpotifyScraperService
from app.services.platform_services.youtube_service import YouTubeService
from app.services.platform_services.platform_services_factory import PlatformServiceFactory
import app.services.platform_services.platform_services_factory as factory_module
from config import Config


@pytest.mark.usefixtures("app")
class TestPlatformServiceFactory:
    """Tests for PlatformServiceFactory to ensure correct return types."""

    def test_get_service_soundcloud_returns_correct_type(self):
        """Test that get_service returns SoundcloudService for soundcloud platform."""
        service = PlatformServiceFactory.get_service("soundcloud")
        # May be MockSoundcloudService due to conftest, but should have the name SoundcloudService
        assert service.__name__ in ('SoundcloudService', 'MockSoundcloudService')

    def test_get_service_spotify_with_credentials_returns_api_service(self, monkeypatch):
        """Test that get_service returns SpotifyAPIService when credentials are configured."""
        # Reload the module to get original implementation without conftest modifications
        importlib.reload(factory_module)
        
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_ID', 'test_client_id')
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_SECRET', 'test_client_secret')
        
        service = PlatformServiceFactory.get_service("spotify")
        assert service == SpotifyApiService

    def test_get_service_spotify_without_credentials_returns_scraper_service(self, monkeypatch):
        """Test that get_service returns SpotifyScraperService when no credentials."""
        # Reload the module to get original implementation without conftest modifications
        importlib.reload(factory_module)
        
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_ID', '')
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_SECRET', '')
        
        service = PlatformServiceFactory.get_service("spotify")
        assert service == SpotifyScraperService

    def test_get_service_youtube_returns_correct_type(self):
        """Test that get_service returns YouTubeService for youtube platform."""
        service = PlatformServiceFactory.get_service("youtube")
        assert service == YouTubeService
        assert service is YouTubeService

    def test_get_service_unsupported_platform_raises_value_error(self):
        """Test that get_service raises ValueError for unsupported platform."""
        with pytest.raises(ValueError, match="Unsupported platform: invalid"):
            PlatformServiceFactory.get_service("invalid")

    def test_get_service_by_url_soundcloud_returns_correct_type(self):
        """Test that get_service_by_url returns SoundcloudService for SoundCloud URLs."""
        urls = [
            "https://soundcloud.com/artist/track",
            "https://m.soundcloud.com/artist/track",
            "https://api.soundcloud.com/tracks/123"
        ]
        for url in urls:
            service = PlatformServiceFactory.get_service_by_url(url)
            # May be MockSoundcloudService due to conftest, but should have the name SoundcloudService
            assert service.__name__ in ('SoundcloudService', 'MockSoundcloudService'), f"Failed for URL: {url}"

    def test_get_service_by_url_spotify_with_credentials_returns_api_service(self, monkeypatch):
        """Test that get_service_by_url returns SpotifyAPIService for Spotify URLs with credentials."""
        # Reload the module to get original implementation without conftest modifications
        importlib.reload(factory_module)
        
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_ID', 'test_client_id')
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_SECRET', 'test_client_secret')
        
        urls = [
            "https://open.spotify.com/playlist/123",
            "https://play.spotify.com/track/456",
            "https://api.spotify.com/v1/playlists/789"
        ]
        for url in urls:
            service = PlatformServiceFactory.get_service_by_url(url)
            assert service == SpotifyApiService, f"Failed for URL: {url}"

    def test_get_service_by_url_spotify_without_credentials_returns_scraper_service(self, monkeypatch):
        """Test that get_service_by_url returns SpotifyScraperService for Spotify URLs without credentials."""
        # Reload the module to get original implementation without conftest modifications
        importlib.reload(factory_module)
        
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_ID', '')
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_SECRET', '')
        
        urls = [
            "https://open.spotify.com/playlist/123",
            "https://play.spotify.com/track/456"
        ]
        for url in urls:
            service = PlatformServiceFactory.get_service_by_url(url)
            assert service == SpotifyScraperService, f"Failed for URL: {url}"

    def test_get_service_by_url_youtube_returns_correct_type(self):
        """Test that get_service_by_url returns YouTubeService for YouTube URLs."""
        urls = [
            "https://www.youtube.com/watch?v=123",
            "https://youtube.com/playlist?list=456",
            "https://youtu.be/789",
            "https://m.youtube.com/watch?v=abc"
        ]
        for url in urls:
            service = PlatformServiceFactory.get_service_by_url(url)
            assert service == YouTubeService, f"Failed for URL: {url}"

    def test_get_service_by_url_invalid_url_raises_value_error(self):
        """Test that get_service_by_url raises ValueError for invalid URLs."""
        invalid_urls = [
            "https://invalid.com/playlist",
            "https://notsoundcloud.com/track",
            "https://example.com"
        ]
        for url in invalid_urls:
            with pytest.raises(ValueError, match="URL Doesn't Look Right"):
                PlatformServiceFactory.get_service_by_url(url)

    def test_get_service_by_url_malformed_url_raises_value_error(self):
        """Test that get_service_by_url handles malformed URLs gracefully."""
        with pytest.raises(ValueError, match="URL Doesn't Look Right"):
            PlatformServiceFactory.get_service_by_url("not a url at all")

    def test_has_spotify_credentials_with_valid_credentials(self, monkeypatch):
        """Test _has_spotify_credentials returns True when credentials are valid."""
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_ID', 'test_client_id')
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_SECRET', 'test_client_secret')
        
        assert PlatformServiceFactory._has_spotify_credentials() is True

    def test_has_spotify_credentials_with_empty_strings(self, monkeypatch):
        """Test _has_spotify_credentials returns False for empty strings."""
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_ID', '')
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_SECRET', '')
        
        assert PlatformServiceFactory._has_spotify_credentials() is False

    def test_has_spotify_credentials_with_whitespace_only(self, monkeypatch):
        """Test _has_spotify_credentials returns False for whitespace-only strings."""
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_ID', '   ')
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_SECRET', '   ')
        
        assert PlatformServiceFactory._has_spotify_credentials() is False

    def test_has_spotify_credentials_with_none_values(self, monkeypatch):
        """Test _has_spotify_credentials returns False for None values."""
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_ID', None)
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_SECRET', None)
        
        assert PlatformServiceFactory._has_spotify_credentials() is False
