import json
import os

current_dir = os.path.dirname(os.path.abspath(__file__))


class MockSpotifyClient:
    """Mock SpotifyClient for SpotifyScraperService testing."""

    def __init__(self):
        self.closed = False

    def get_playlist_info(self, url):
        """Mock get_playlist_info method."""
        # Extract playlist ID from URL
        if "playlist/" in url:
            playlist_id = url.split('/')[-1].split('?')[0]
        else:
            raise Exception("Failed to extract playlist data from page using any method")

        # Handle test cases
        if playlist_id == "error" or playlist_id == "2132123":
            raise Exception("Failed to extract playlist data from page using any method")

        if playlist_id == "empty":
            return {
                "id": "empty",
                "name": "Empty Playlist",
                "uri": "spotify:playlist:empty",
                "type": "playlist",
                "images": [],
                "tracks": [],
                "track_count": 0,
                "duration_ms": 0
            }

        # Load mock data
        file_path = os.path.join(current_dir, "../mock_data", f"spotify_scraper_playlist_{playlist_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)

        raise Exception(f"Mock data not found for playlist_id: {playlist_id}")

    def close(self):
        """Mock close method."""
        self.closed = True


class MockSpotifyBulkOperations:
    """Mock SpotifyBulkOperations for testing."""

    def process_urls(self, urls, operation="info"):
        """Mock process_urls method."""
        # Load mock bulk track data
        file_path = os.path.join(current_dir, "../mock_data", "spotify_scraper_tracks_bulk.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                all_data = json.load(file)
                
                # Filter results to match requested URLs
                filtered_results = {}
                for url in urls:
                    if url in all_data.get('results', {}):
                        filtered_results[url] = all_data['results'][url]
                
                return {
                    "total_urls": len(urls),
                    "processed": len(filtered_results),
                    "failed": 0,
                    "results": filtered_results
                }
        
        return {
            "total_urls": len(urls),
            "processed": 0,
            "failed": len(urls),
            "results": {}
        }
