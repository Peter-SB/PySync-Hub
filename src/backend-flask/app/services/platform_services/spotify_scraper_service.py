import hashlib
import json
import logging
import os
import re
import requests
from typing import List, Dict, Any, Optional

from spotify_scraper import SpotifyClient
from spotify_scraper.utils.common import SpotifyBulkOperations

from app.repositories.playlist_repository import PlaylistRepository
from app.services.platform_services.spotify_base_service import BaseSpotifyService
from app.extensions import emit_error_message
from app.repositories.track_repository import TrackRepository


logger = logging.getLogger(__name__)


class SpotifyScraperService(BaseSpotifyService):
    """Spotify service using web scraping (no API keys required, slower)."""

    @staticmethod
    def _get_scraper_client() -> SpotifyClient:
        """Create and return a SpotifyClient instance."""
        return SpotifyClient()


    @staticmethod
    def _get_playlist_cover_image(playlist_info: Dict[str, Any], playlist_url: str, client: SpotifyClient) -> Optional[str]:
        """
        Get the cover image for a Spotify playlist with multiple fallback strategies.
        
        1. Try to get image from playlist_info['images']
        2. If no image, try to scrape mosaic.scdn.co URL from Spotify playlist page
        3. If still no image, fall back to first track's album art
        
        Args:
            playlist_info: Playlist data from scraper
            playlist_url: URL of the playlist
            client: SpotifyClient instance
            
        Returns:
            Image URL or None
        """
        image_url = None
        
        # Strategy 1: Try playlist images from scraper response
        if playlist_info.get('images') and len(playlist_info['images']) > 0:
            # Find 300x300 image or closest match
            for img in playlist_info['images']:
                if img.get('width') == 300 and img.get('height') == 300:
                    image_url = img.get('url')
                    break
            # Fallback to first image if no 300x300 found
            if not image_url and playlist_info['images']:
                image_url = playlist_info['images'][0].get('url')
        
        # Strategy 2: Try to scrape mosaic image from Spotify playlist page
        if not image_url:
            image_url = SpotifyScraperService._scrape_mosaic_image_from_playlist_page(playlist_url)
        
        # Strategy 3: Fall back to first track's album art
        if not image_url:
            tracks = playlist_info.get('tracks', [])
            track = tracks[0] if tracks else None
            if track:
                try:
                    track_id = track.get('uri').split(':')[-1]
                    track_url = SpotifyScraperService._get_track_url_from_id(track_id)
                    if track_full := client.get_track_info(track_url):
                        if track_full.get('album', {}).get('images'):
                            # Prefer 300x300 or similar size
                            images = track_full['album']['images']
                            for img in images:
                                if img.get('width') == 300 or img.get('height') == 300:
                                    image_url = img.get('url')
                                    break
                            # Fallback to second image (usually medium size)
                            if not image_url and len(images) > 1:
                                image_url = images[1].get('url')
                            # Final fallback to first image
                            elif not image_url and images:
                                image_url = images[0].get('url')
                            logger.info("Using first track's album art as playlist cover")
                except Exception as e:
                    logger.warning("Error getting first track's album art: %s", e)
        
        return image_url

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
                
                # Get cover image using the extracted function
                image_url = SpotifyScraperService._get_playlist_cover_image(playlist_info, url, client)
                
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
        Returns a ordered list of dictionaries with track information.
        
        Args:
            url: Playlist URL
        
        Raises:
            ValueError: If the playlist is a private/saved tracks playlist
        """
        try:
            logger.info("Fetching tracks for playlist %s using scraper", url)
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
                playlist_info = client.get_playlist_info(url)
                logger.debug(f"playlist_info: {json.dumps(playlist_info, indent=2)}")
                if not playlist_info.get('tracks'):
                    logger.warning("No tracks found in for playlist %s", url)
                    return []
                
                tracks_ids = [SpotifyScraperService._get_track_id_from_uri(track.get('uri', '')) for track in playlist_info.get('tracks', [])]
                playlist_tracks = []
                tracks_urls_to_fetch = []

                if track_limit and track_limit < len(tracks_ids):
                    tracks_ids = tracks_ids[:track_limit]

                # First, check which tracks are already in the DB and which need fetching
                for track_platform_id in tracks_ids:
                    if track:= TrackRepository.get_track_by_platform_id(track_platform_id):
                        playlist_tracks.append(track.to_dict() if hasattr(track, 'to_dict') else track)
                    else:
                        # Temporarily add platform_id, will replace with full data after fetching
                        playlist_tracks.append(track_platform_id)
                        tracks_urls_to_fetch.append(SpotifyScraperService._get_track_url_from_id(track_platform_id))

                # Fetch and add missing track info in bulk
                fetched_tracks = SpotifyScraperService.bulk_fetch_track_info(tracks_urls_to_fetch)
                for platform_id, track_info in fetched_tracks.items():
                    if platform_id in tracks_ids:
                        index = playlist_tracks.index(platform_id)
                        playlist_tracks[index] = track_info
                    else:
                        logger.warning("Fetched track ID %s not found in original playlist IDs", platform_id)


                return playlist_tracks
            finally:
                client.close()
        except ValueError:
            raise
        except Exception as e:
            logger.error("Error fetching tracks for playlist %s: %s", url, e, exc_info=True)
            raise

    @staticmethod
    def bulk_fetch_track_info(track_urls: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Bulk fetch track info using Spotify scraper.
        
        Args:
            track_urls: List of Spotify track platform IDs.
        
        Returns:
            Dictionary mapping track URL to track data dictionary.
        """
        bulk = SpotifyBulkOperations()
        results = bulk.process_urls(track_urls, operation="info")
        
        track_data_map = {}
        for track_url, result_data in results.get('results', {}).items():
            if 'info' not in result_data:
                continue
            track_info = result_data['info']
            track_data = SpotifyScraperService._format_track_data_from_scraper(track_info)
            track_platform_id = SpotifyScraperService._get_track_id_from_uri(track_info.get('uri', ''))
            track_data_map[track_platform_id] = track_data
        
        return track_data_map


    @staticmethod
    def _get_track_url_from_id(track_id: str) -> str:
        return f"https://open.spotify.com/track/{track_id}"
    

    @staticmethod
    def _get_track_url(track) -> Optional[str]:
        track_uri = track.get('uri', '')
        if track_uri and track_uri.startswith('spotify:track:'):
            track_id = SpotifyScraperService._get_track_id_from_uri(track_uri)
            return SpotifyScraperService._get_track_url_from_id(track_id)

        logger.warning("Invalid track URI: %s", track.get('uri', ''))
        return None
    
    @staticmethod
    def _get_track_id_from_uri(track_uri: str) -> Optional[str]:
        if track_uri.startswith('spotify:track:'):
            return track_uri.split(':')[-1]
        return None

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
            'duration_ms': track_info.get('duration_ms') or track_info.get('duration'),
        }


    @staticmethod
    def _scrape_mosaic_image_from_playlist_page(playlist_url: str) -> Optional[str]:
        """
        Scrape the mosaic image URL from the Spotify playlist page HTML.
        
        This method is extracted to allow easy stubbing in tests.
        
        Args:
            playlist_url: URL of the Spotify playlist
            
        Returns:
            Mosaic image URL or None
        """
        try:
            response = requests.get(playlist_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }, timeout=10)
            if response.status_code == 200:
                # Look for mosaic.scdn.co URL in the HTML
                # Pattern matches: https://mosaic.scdn.co/300/...
                mosaic_pattern = r'https://mosaic\.scdn\.co/300/[a-f0-9]+'
                match = re.search(mosaic_pattern, response.text)
                if match:
                    image_url = match.group(0)
                    logger.info("Found mosaic image: %s", image_url)
                    return image_url
                else:
                    logger.debug("No mosaic image found in Spotify page HTML")
            else:
                logger.warning("Failed to fetch Spotify playlist page, status: %d", response.status_code)
        except Exception as e:
            logger.warning("Error scraping playlist page for mosaic image: %s", e)
        
        return None
    

    @staticmethod
    def search_track(query: str, limit: int = 3) -> list[dict]:
        """ 
        Search for track using query. Not supported with scraper. 
        """
        raise NotImplementedError("Search track not possible for SpotifyScraperService.")

    @staticmethod
    def get_track_by_url(track_url: str) -> Dict[str, Any]:
        """Fetch a single track by Spotify URL using the scraper."""
        track_id = SpotifyScraperService._extract_track_id(track_url)
        if not track_id:
            raise ValueError("Invalid Spotify track URL.")

        resolved_url = track_url
        if "open.spotify.com" not in track_url:
            resolved_url = SpotifyScraperService._get_track_url_from_id(track_id)

        client = SpotifyScraperService._get_scraper_client()
        try:
            track_info = client.get_track_info(resolved_url)
        finally:
            client.close()

        if not track_info:
            raise ValueError("Track not found on Spotify.")

        return SpotifyScraperService._format_track_data_from_scraper(track_info)
