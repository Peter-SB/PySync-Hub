# Platform Services

This directory contains services for interacting with the various music streaming platforms (SoundCloud, Spotify, YouTube, etc.).

## Architecture

All platform services follow a common interface defined by `BasePlatformService`, which ensures consistency across different platforms and allow for polymorphism.

### Base Interface

The `BasePlatformService` abstract base class defines two required methods:

1. **`get_playlist_data(url: str) -> Dict[str, Any]`**
   - Fetches metadata for a playlist (name, image, track count, etc.)
   - Returns a standardized dictionary with playlist information

2. **`get_playlist_tracks(url: str) -> List[Dict[str, Any]]`**
   - Fetches all tracks in a playlist
   - Returns a list of track dictionaries with standardized fields

3. **`search_track(query: str) -> List[Dict[str, Any]]`**
   - Searches a given platform for tracks given a query string.
   - Return, like get_playlist_tracks, a list of track dictionaries with standardized fields
   - Not implemented for spotify scraper.

### Platform Services

#### Spotify (`spotify_base_service.py`, `spotify_api_service.py`, `spotify_scraper_service.py`)
- `BaseSpotifyService` extends `BasePlatformService` with Spotify-specific shared functionality
- `SpotifyApiService` - Uses official Spotify API (requires credentials)
- `SpotifyScraperService` - Uses web scraping (fallback when no credentials)

#### SoundCloud (`soundcloud_service.py`)
- Implements `BasePlatformService`
- Handles SoundCloud playlists and liked tracks
- Uses web scraping and SoundCloud API v2

#### YouTube (`youtube_service.py`)
- Implements `BasePlatformService`
- Fetches YouTube playlist data using yt-dlp
- Handles unavailable/private videos gracefully


### Factory Pattern

The `PlatformServiceFactory` provides methods to get the appropriate service:

```python
service = PlatformServiceFactory.get_service('soundcloud')
service = PlatformServiceFactory.get_service_by_url('https://soundcloud.com/...')
```

## Benefits of the Interface Pattern

1. **Consistency**: All platforms follow the same interface
2. **Type Safety**: Type hints ensure proper usage
3. **Extensibility**: Easy to add new platforms
4. **Maintainability**: Changes to the interface affect all implementations
5. **Factory Pattern**: Centralized service selection logic
6. **Testing**: Easy to mock and test individual services
