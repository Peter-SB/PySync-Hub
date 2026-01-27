import logging
from typing import List, Dict, Any

from spotify_scraper import SpotifyClient
from spotify_scraper.utils.common import SpotifyBulkOperations

from app.repositories.playlist_repository import PlaylistRepository
from app.services.platform_services.base_spotify_service import BaseSpotifyService
from app.extensions import emit_error_message

logger = logging.getLogger(__name__)


class SpotifyScraperService(BaseSpotifyService):
    """Spotify service using web scraping (no API keys required, slower)."""

    @staticmethod
    def _get_scraper_client() -> SpotifyClient:
        """Create and return a SpotifyClient instance."""
        return SpotifyClient()

    @staticmethod
    def get_playlist_data(url: str) -> Dict[str, Any]:
        """
        Fetches playlist metadata using the scraper.
        
        Raises:
            ValueError: If the playlist is a private/saved tracks playlist
            Exception: If the playlist cannot be found or accessed
        """
        try:
            # Check for private playlists - not supported with scraper
            if "collection/tracks" in url:
                error = "Private playlists (Liked Songs) are not supported without Spotify API credentials. Please add your Spotify API keys in Settings."
                emit_error_message(url, error)
                raise ValueError(error)

            client = SpotifyScraperService._get_scraper_client()
            
            try:
                # Get playlist info
                playlist_info = client.get_playlist_info(url)
                
                # Extract playlist ID from URL or URI
                playlist_id = SpotifyScraperService._extract_playlist_id(url)
                
                # Handle missing cover images
                image_url = None
                if playlist_info.get('images') and len(playlist_info['images']) > 0:
                    # Find 300x300 image or closest match
                    for img in playlist_info['images']:
                        if img.get('width') == 300 and img.get('height') == 300:
                            image_url = img.get('url')
                            break
                    # Fallback to first image if no 300x300 found
                    if not image_url and playlist_info['images']:
                        image_url = playlist_info['images'][0].get('url')
                
                # If no playlist cover, we'll use the first track's album art later if needed
                # This is handled in the application layer
                
                data = {
                    'name': playlist_info.get('name', 'Unknown Playlist'),
                    'external_id': playlist_id,
                    'image_url': image_url,
                    'track_count': playlist_info.get('track_count', 0),
                    'url': url,
                    'platform': 'spotify'
                }
                
                return data
                
            finally:
                client.close()

        except ValueError:
            # Re-raise ValueError for private playlists
            raise
        except Exception as e:
            error_msg = str(e)
            # Check if it's a "not found" error
            if "Failed to extract playlist data" in error_msg or "404" in error_msg:
                raise Exception(
                    f"Playlist not found. Please check the playlist is public or try another URL. Error: {e}"
                )
            raise

    @staticmethod
    def get_playlist_tracks(url: str) -> List[Dict[str, Any]]:
        """
        Fetches the tracks for a given Spotify playlist using the scraper.
        Only scrapes tracks not already in the database.
        Returns a list of dictionaries with track information.
        
        Raises:
            ValueError: If the playlist is a private/saved tracks playlist
        """
        try:
            logger.info("Fetching tracks for playlist %s using scraper (skip existing)", url)
            # Check for private playlists - not supported with scraper
            if "collection/tracks" in url:
                raise ValueError(
                    "Private playlists (Liked Songs) are not supported without Spotify API credentials. "
                    "Please add your Spotify API keys in Settings."
                )

            playlist = PlaylistRepository.get_playlist_by_url(url)
            track_limit = playlist.to_dict().get('track_limit', None)
            date_limit = playlist.to_dict().get('date_limit', None)

            client = SpotifyScraperService._get_scraper_client()
            try:
                # Get basic playlist info to get track URIs
                playlist_info = client.get_playlist_info(url)
                if not playlist_info.get('tracks'):
                    logger.info("Playlist has no tracks")
                    return []

                # Extract track IDs and URLs for bulk fetching
                track_id_url_map = {}
                for track in playlist_info['tracks']:
                    track_uri = track.get('uri', '')
                    if track_uri and track_uri.startswith('spotify:track:'):
                        track_id = track_uri.split(':')[-1]
                        track_url = f"https://open.spotify.com/track/{track_id}"
                        track_id_url_map[track_id] = track_url

                if not track_id_url_map:
                    logger.info("No valid track URIs found")
                    return []

                # Apply track limit if specified
                track_ids = list(track_id_url_map.keys())
                if track_limit and track_limit < len(track_ids):
                    track_ids = track_ids[:track_limit]

                # Query DB for existing tracks by platform_id (track_id)
                # Assumes PlaylistRepository or TrackRepository has a method to check for existing track IDs
                from app.repositories.track_repository import TrackRepository
                existing_ids = set(TrackRepository.get_existing_spotify_ids(track_ids))

                # Only scrape tracks not in DB
                new_track_ids = [tid for tid in track_ids if tid not in existing_ids]
                new_track_urls = [track_id_url_map[tid] for tid in new_track_ids]

                logger.info("%d/%d tracks already in DB, scraping %d new tracks", len(existing_ids), len(track_ids), len(new_track_urls))

                if not new_track_urls:
                    logger.info("No new tracks to scrape")
                    return []

                # Fetch full track info using bulk operations (faster than individual requests)
                bulk = SpotifyBulkOperations()
                results = bulk.process_urls(new_track_urls, operation="info")

                # Transform scraped data to match API format
                tracks_data = []
                for track_url, result_data in results.get('results', {}).items():
                    if 'info' not in result_data:
                        continue
                    track_info = result_data['info']
                    # Transform to standard format
                    track_data = SpotifyScraperService._format_track_data_from_scraper(track_info)
                    # Apply date limit if specified (not supported by scraper)
                    if date_limit is not None:
                        logger.warning(
                            "Date filtering is not supported with Spotify scraper. "
                            "Please use Spotify API credentials for this feature."
                        )
                    tracks_data.append(track_data)

                logger.info("Fetched %d new tracks for playlist using scraper", len(tracks_data))
                return tracks_data
            finally:
                client.close()
        except ValueError:
            # Re-raise ValueError for private playlists
            raise
        except Exception as e:
            logger.error("Error fetching tracks for playlist %s: %s", url, e, exc_info=True)
            raise

    @staticmethod
    def _format_track_data_from_scraper(track_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format track data from scraper to match the standardized format.
        
        The scraper returns data in a slightly different structure than the API.
        """
        # Get the best album art (prefer 300x300)
        album_art_url = None
        if track_info.get('album', {}).get('images'):
            images = track_info['album']['images']
            for img in images:
                if img.get('width') == 300 and img.get('height') == 300:
                    album_art_url = img.get('url')
                    break
            # Fallback to first image
            if not album_art_url and images:
                album_art_url = images[0].get('url')
        
        return {
            'platform_id': track_info.get('id', ''),
            'platform': 'spotify',
            'name': track_info.get('name', 'Unknown Track'),
            'artist': ", ".join([artist['name'] for artist in track_info.get('artists', [])]),
            'album': track_info.get('album', {}).get('name'),
            'album_art_url': album_art_url,
            'download_url': None,
            'added_on': None,  # Scraper doesn't provide this info
        }
