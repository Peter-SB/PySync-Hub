import pytest

from app.models import Playlist
from app.extensions import db
from app.services.platform_services.spotify_scraper_service import SpotifyScraperService
from app.services.platform_services.platform_services_factory import PlatformServiceFactory


@pytest.mark.usefixtures("client", "init_database")
class TestSpotifyScraperService:
    """Tests for SpotifyScraperService."""

    def test_get_playlist_data_with_valid_playlist(self, app, monkeypatch):
        """Test getting playlist data with a valid playlist."""
        from tests.mocks.mock_spotify_scraper import MockSpotifyClient
        
        # Mock the scraper client
        monkeypatch.setattr(
            "app.services.platform_services.spotify_scraper_service.SpotifyClient",
            MockSpotifyClient
        )
        
        with app.app_context():
            url = "https://open.spotify.com/playlist/1zfCA5tZu2QyWINEjpzDVd"
            data = SpotifyScraperService.get_playlist_data(url)
            
            assert data['name'] == "Test Scraper Playlist"
            assert data['external_id'] == "1zfCA5tZu2QyWINEjpzDVd"
            assert data['platform'] == "spotify"
            assert data['track_count'] == 2
            assert data['image_url'] is not None
            assert "300" in data['image_url'] or data['image_url'].endswith("2723a5")

    def test_get_playlist_data_with_empty_playlist(self, app, monkeypatch):
        """Test getting playlist data with an empty playlist."""
        from tests.mocks.mock_spotify_scraper import MockSpotifyClient
        
        # Mock the scraper client
        monkeypatch.setattr(
            "app.services.platform_services.spotify_scraper_service.SpotifyClient",
            MockSpotifyClient
        )
        
        with app.app_context():
            url = "https://open.spotify.com/playlist/empty"
            data = SpotifyScraperService.get_playlist_data(url)
            
            assert data['name'] == "Empty Playlist"
            assert data['track_count'] == 0
            assert data['image_url'] is None

    def test_get_playlist_data_with_not_found(self, app, monkeypatch):
        """Test getting playlist data with a non-existent playlist."""
        from tests.mocks.mock_spotify_scraper import MockSpotifyClient
        
        # Mock the scraper client
        monkeypatch.setattr(
            "app.services.platform_services.spotify_scraper_service.SpotifyClient",
            MockSpotifyClient
        )
        
        with app.app_context():
            url = "https://open.spotify.com/playlist/2132123"
            with pytest.raises(Exception) as exc_info:
                SpotifyScraperService.get_playlist_data(url)
            
            assert "Playlist not found" in str(exc_info.value)

    def test_get_playlist_data_with_private_playlist(self, app, monkeypatch):
        """Test that private playlists (liked songs) raise an error."""
        from tests.mocks.mock_spotify_scraper import MockSpotifyClient
        
        # Mock the scraper client
        monkeypatch.setattr(
            "app.services.platform_services.spotify_scraper_service.SpotifyClient",
            MockSpotifyClient
        )
        
        with app.app_context():
            url = "https://open.spotify.com/collection/tracks"
            with pytest.raises(ValueError) as exc_info:
                SpotifyScraperService.get_playlist_data(url)
            
            assert "Private playlists" in str(exc_info.value)
            assert "Liked Songs" in str(exc_info.value)

    def test_get_playlist_tracks(self, app, monkeypatch):
        """Test getting playlist tracks."""
        from tests.mocks.mock_spotify_scraper import MockSpotifyClient, MockSpotifyBulkOperations
        
        # Mock the scraper client and bulk operations
        monkeypatch.setattr(
            "app.services.platform_services.spotify_scraper_service.SpotifyClient",
            MockSpotifyClient
        )
        monkeypatch.setattr(
            "app.services.platform_services.spotify_scraper_service.SpotifyBulkOperations",
            MockSpotifyBulkOperations
        )
        
        with app.app_context():
            # Create a test playlist in the database
            playlist = Playlist(
                id=1,
                name="Test Playlist",
                platform="spotify",
                external_id="1zfCA5tZu2QyWINEjpzDVd",
                url="https://open.spotify.com/playlist/1zfCA5tZu2QyWINEjpzDVd",
                download_status="ready"
            )
            db.session.add(playlist)
            db.session.commit()
            
            # Get tracks
            tracks = SpotifyScraperService.get_playlist_tracks(playlist.url)
            
            assert len(tracks) == 2
            assert tracks[0]['name'] == "Track One"
            assert tracks[0]['artist'] == "Artist One"
            assert tracks[0]['platform_id'] == "3vkQ5DAB1qQMYO4Mr9zJN6"
            assert tracks[0]['album'] == "Album One"
            assert tracks[0]['album_art_url'] is not None
            assert tracks[1]['name'] == "Track Two"

    def test_get_playlist_tracks_with_empty_playlist(self, app, monkeypatch):
        """Test getting tracks from an empty playlist."""
        from tests.mocks.mock_spotify_scraper import MockSpotifyClient, MockSpotifyBulkOperations
        
        # Mock the scraper client and bulk operations
        monkeypatch.setattr(
            "app.services.platform_services.spotify_scraper_service.SpotifyClient",
            MockSpotifyClient
        )
        monkeypatch.setattr(
            "app.services.platform_services.spotify_scraper_service.SpotifyBulkOperations",
            MockSpotifyBulkOperations
        )
        
        with app.app_context():
            # Create a test playlist in the database
            playlist = Playlist(
                id=1,
                name="Empty Playlist",
                platform="spotify",
                external_id="empty",
                url="https://open.spotify.com/playlist/empty",
                download_status="ready"
            )
            db.session.add(playlist)
            db.session.commit()
            
            # Get tracks
            tracks = SpotifyScraperService.get_playlist_tracks(playlist.url)
            
            assert len(tracks) == 0

    def test_get_playlist_tracks_with_private_playlist(self, app, monkeypatch):
        """Test that getting tracks from private playlists raises an error."""
        from tests.mocks.mock_spotify_scraper import MockSpotifyClient
        
        # Mock the scraper client
        monkeypatch.setattr(
            "app.services.platform_services.spotify_scraper_service.SpotifyClient",
            MockSpotifyClient
        )
        
        with app.app_context():
            # Create a test playlist in the database
            playlist = Playlist(
                id=1,
                name="Liked Songs",
                platform="spotify",
                external_id="liked-songs",
                url="https://open.spotify.com/collection/tracks",
                download_status="ready"
            )
            db.session.add(playlist)
            db.session.commit()
            
            # Try to get tracks
            with pytest.raises(ValueError) as exc_info:
                SpotifyScraperService.get_playlist_tracks(playlist.url)
            
            assert "Private playlists" in str(exc_info.value)


@pytest.mark.usefixtures("client", "init_database")
class TestPlatformServiceFactory:
    """Tests for PlatformServiceFactory Spotify service selection."""

    def test_has_spotify_credentials_with_valid_credentials(self, app, monkeypatch):
        """Test that _has_spotify_credentials returns True when credentials are present."""
        from app.services.platform_services.platform_services_factory import PlatformServiceFactory
        from config import Config
        
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_ID', 'test_client_id')
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_SECRET', 'test_client_secret')
        
        with app.app_context():
            assert PlatformServiceFactory._has_spotify_credentials()

    def test_has_spotify_credentials_without_credentials(self, app, monkeypatch):
        """Test that _has_spotify_credentials returns False when credentials are missing."""
        from app.services.platform_services.platform_services_factory import PlatformServiceFactory
        from config import Config
        
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_ID', None)
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_SECRET', None)
        
        with app.app_context():
            assert not PlatformServiceFactory._has_spotify_credentials()

    def test_has_spotify_credentials_with_empty_credentials(self, app, monkeypatch):
        """Test that _has_spotify_credentials returns False when credentials are empty strings."""
        from app.services.platform_services.platform_services_factory import PlatformServiceFactory
        from config import Config
        
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_ID', '')
        monkeypatch.setattr(Config, 'SPOTIFY_CLIENT_SECRET', '')
        
        with app.app_context():
            assert not PlatformServiceFactory._has_spotify_credentials()

    def test_factory_by_url_with_spotify_url(self, app):
        """Test that factory returns correct service for Spotify URL."""
        from app.services.platform_services.spotify_api_service import SpotifyAPIService
        from app.services.platform_services.platform_services_factory import PlatformServiceFactory
        
        with app.app_context():
            # The conftest ensures API service is returned
            service = PlatformServiceFactory.get_service_by_url(
                'https://open.spotify.com/playlist/1zfCA5tZu2QyWINEjpzDVd'
            )
            assert service == SpotifyAPIService
