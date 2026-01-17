import pytest
from urllib.parse import urlparse

from app.models import Playlist
from app.repositories.playlist_repository import PlaylistRepository
from app.services.playlist_manager_service import PlaylistManagerService
from app.services.platform_services.youtube_service import YouTubeService


@pytest.mark.usefixtures("client", "init_database")
class TestYouTubePlaylistImport:
    """
    Tests for YouTube playlist import functionality.
    
    Tests focus on full happy paths and edge cases as per requirements:
    - Happy path: importing a valid public playlist
    - Edge case: playlist with unavailable/private videos
    - Edge case: empty playlist
    - Edge case: invalid URL
    """

    def test_add_valid_youtube_playlist(self, client):
        """
        Happy path: Test adding a valid YouTube playlist.
        Verifies that playlist metadata and tracks are correctly imported.
        """
        # Add playlist via API
        response = client.post('/api/playlists', 
                              json={"url_or_id": "https://www.youtube.com/playlist?list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"})
        
        assert response.status_code == 201
        playlists = response.get_json()
        
        # Verify playlist was added
        assert any(p["external_id"] == "PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j" for p in playlists)
        
        # Verify playlist details in database
        added_playlist = Playlist.query.filter_by(external_id="PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j").first()
        assert added_playlist is not None
        assert added_playlist.name == "Test YouTube Playlist"
        assert added_playlist.track_count == 3
        assert added_playlist.platform == "youtube"
        assert added_playlist.image_url is not None
        
        # Verify tracks were added
        assert len(added_playlist.tracks) == 3
        
        # Verify track details
        track_names = [pt.track.name for pt in added_playlist.tracks]
        assert "Never Gonna Give You Up" in track_names
        assert "Me at the zoo" in track_names
        assert "PSY - GANGNAM STYLE" in track_names

    def test_add_youtube_playlist_with_unavailable_videos(self, client):
        """
        Edge case: Test adding a playlist that contains unavailable/private videos.
        Verifies that only available videos are imported.
        """
        # Add playlist with some unavailable videos
        response = client.post('/api/playlists',
                              json={"url_or_id": "https://www.youtube.com/playlist?list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j&unavailable=true"})
        
        assert response.status_code == 201
        playlists = response.get_json()
        
        # Verify playlist was added
        added_playlist = Playlist.query.filter_by(platform="youtube").first()
        assert added_playlist is not None
        assert added_playlist.name == "Test YouTube Playlist with Unavailable Videos"
        
        # Verify only available videos were added (2 out of 3)
        assert added_playlist.track_count == 2
        assert len(added_playlist.tracks) == 2
        
        # Verify the available tracks
        track_names = [pt.track.name for pt in added_playlist.tracks]
        assert "Never Gonna Give You Up" in track_names
        assert "Me at the zoo" in track_names

    def test_add_empty_youtube_playlist(self, client):
        """
        Edge case: Test adding an empty YouTube playlist.
        Verifies that appropriate error is returned.
        """
        response = client.post('/api/playlists',
                              json={"url_or_id": "https://www.youtube.com/playlist?list=PLempty"})
        
        assert response.status_code == 400
        error_message = response.get_json().get("error")
        assert "empty" in error_message.lower() or "error" in error_message.lower()

    def test_add_invalid_youtube_url(self, client):
        """
        Edge case: Test adding an invalid YouTube playlist URL.
        Verifies that appropriate error is returned.
        """
        response = client.post('/api/playlists',
                              json={"url_or_id": "https://www.youtube.com/playlist?list=invalid"})
        
        assert response.status_code == 400
        error_message = response.get_json().get("error")
        assert error_message is not None

    def test_add_malformed_youtube_url(self, client):
        """
        Edge case: Test adding a malformed YouTube URL.
        Verifies that appropriate error is returned.
        """
        response = client.post('/api/playlists',
                              json={"url_or_id": "not-a-valid-url"})
        
        assert response.status_code == 400
        error_message = response.get_json().get("error")
        assert "URL Doesn't Look Right" in error_message or "error" in error_message.lower()

    def test_add_youtube_playlist_already_exists(self, client):
        """
        Test that adding the same YouTube playlist twice returns appropriate error.
        """
        # Add playlist first time
        response1 = client.post('/api/playlists',
                               json={"url_or_id": "https://www.youtube.com/playlist?list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"})
        assert response1.status_code == 201
        
        # Try to add same playlist again
        response2 = client.post('/api/playlists',
                               json={"url_or_id": "https://www.youtube.com/playlist?list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"})
        assert response2.status_code == 400
        error_message = response2.get_json().get("error")
        assert error_message == "Playlist Already Added"

    def test_sync_youtube_playlist(self, app):
        """
        Test syncing a YouTube playlist to update metadata and tracks.
        """
        fake_playlist = Playlist(
            id=1,
            name="Old YouTube Playlist Name",
            platform="youtube",
            external_id="PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j",
            image_url="http://oldimage.com/image.png",
            track_count=0,
            url="https://www.youtube.com/playlist?list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j",
            download_status="ready"
        )
        
        with app.app_context():
            from app.extensions import db
            db.session.add(fake_playlist)
            db.session.commit()

            # Sync the playlist
            playlist_response = PlaylistManagerService.sync_playlists([fake_playlist])
            assert playlist_response[0].name == "Test YouTube Playlist"

            # Verify database was updated
            updated_playlist = Playlist.query.filter_by(external_id="PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j").first()
            assert updated_playlist.name == "Test YouTube Playlist"
            assert updated_playlist.track_count == 3

    def test_youtube_url_variations(self, client):
        """
        Test that various YouTube URL formats are handled correctly.
        """
        # Test standard playlist URL
        url1 = "https://www.youtube.com/playlist?list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"
        response = client.post('/api/playlists', json={"url_or_id": url1})
        assert response.status_code == 201
        
        # Test youtu.be short URL format (if supported)
        url2 = "https://youtu.be/playlist?list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"
        response2 = client.post('/api/playlists', json={"url_or_id": url2})
        # Should either work or give a clear error
        assert response2.status_code in [201, 400]

    def test_youtube_playlist_track_metadata(self, client):
        """
        Test that YouTube track metadata is correctly formatted.
        """
        response = client.post('/api/playlists',
                              json={"url_or_id": "https://www.youtube.com/playlist?list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"})
        
        assert response.status_code == 201
        
        # Get the playlist
        playlist = Playlist.query.filter_by(platform="youtube").first()
        tracks = [pt.track for pt in playlist.tracks]
        
        # Verify track metadata structure
        for track in tracks:
            assert track.platform == "youtube"
            assert track.platform_id is not None
            assert track.name is not None
            assert track.artist is not None
            assert track.download_url is not None
            # Verify YouTube URL using proper parsing to avoid sanitization issues
            parsed_url = urlparse(track.download_url)
            hostname = (parsed_url.hostname or "").lower()
            # Check if hostname is exactly youtube.com/youtu.be or a subdomain
            valid_youtube_domain = (
                hostname == "youtube.com" or hostname.endswith(".youtube.com") or
                hostname == "youtu.be" or hostname.endswith(".youtu.be")
            )
            assert valid_youtube_domain, f"Invalid YouTube URL: {track.download_url}"
            # YouTube doesn't have album info
            assert track.album is None

@pytest.mark.no_youtube_mock
class TestYouTubeService:
    def test_extract_playlist_id(self):
        """ Test the YouTube playlist ID extraction logic """

        # Various URL formats
        playlist_id = "PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"
        urls = [
            (f"https://www.youtube.com/playlist?list={playlist_id}", playlist_id),
            (f"https://youtube.com/playlist?list={playlist_id}", playlist_id),
            (f"https://www.youtube.com/watch?v=5K9c5yYFFsE&list={playlist_id}", playlist_id),
            (playlist_id, playlist_id),
        ]

        for url, expected_id in urls:
            extracted_id = YouTubeService._extract_playlist_id(url)
            assert extracted_id == expected_id, f"Failed to extract ID from {url}"


    def test_get_playlist_data_with_ytdlp(self):
        """  Given a youtube playlist URL, extract the playlist info and tracks using yt-dlp to confirm our service logic and data formatting """

        playlist_url_from_vid = "https://www.youtube.com/watch?v=5K9c5yYFFsE&list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"

        playlist_url_exact = "https://www.youtube.com/playlist?list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"

        playlist_data = YouTubeService.get_playlist_data(playlist_url_from_vid)

        # Check playlist data format
        assert isinstance(playlist_data, dict)
        assert isinstance(playlist_data.get('name'), str)
        assert isinstance(playlist_data.get('external_id'), str)
        assert isinstance(playlist_data.get('track_count'), int)

        # Verify expected playlist data
        assert playlist_data['external_id'] == "PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"
        assert playlist_data['platform'] == "youtube"
        assert playlist_data['name'] == "UKF On Air: Drum & Bass 2017"
        assert playlist_data['track_count'] == 3

    def test_get_playlist_data_with_ytdlp_unlisted(self):
        """  Given a youtube playlist URL, extract the playlist info and tracks using yt-dlp to confirm our service logic and data formatting """

        playlist_url_from_vid = "https://www.youtube.com/watch?v=05_eHt-46IY&list=PL6GqXsUnxEXJv6DqfIWHUCqw-boUyqnQg"

        playlist_url_exact = "https://www.youtube.com/playlist?list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"

        playlist_data = YouTubeService.get_playlist_data(playlist_url_from_vid)

        # Check playlist data format
        assert isinstance(playlist_data, dict)
        assert isinstance(playlist_data.get('name'), str)
        assert isinstance(playlist_data.get('external_id'), str)
        assert isinstance(playlist_data.get('track_count'), int)

    def test_get_playlist_tracks_with_ytdlp(self):
        """ Given a youtube playlist URL, extract the playlist tracks using yt-dlp to confirm our service logic and data formatting """

        playlist_url_from_vid = "https://www.youtube.com/watch?v=5K9c5yYFFsE&list=PLaL5A3VjmybdLqd12jLWBoLCXfZDpYs3j"

        tracks_data = YouTubeService.get_playlist_tracks(playlist_url_from_vid)

        # Check tracks data format
        assert isinstance(tracks_data, list)
        assert len(tracks_data) == 3

        for track in tracks_data:
            assert isinstance(track, dict)
            assert isinstance(track.get('platform_id'), str)
            assert isinstance(track.get('platform'), str)
            assert isinstance(track.get('name'), str)
            assert isinstance(track.get('artist'), str)
            assert track.get('album') is None  # YouTube doesn't have album info
            assert isinstance(track.get('download_url'), str)


    def test_get_playlist_tracks_with_ytdlp_unlisted(self):
        """ Given a youtube playlist URL, extract the playlist tracks using yt-dlp to confirm our service logic and data formatting """

        playlist_url_from_vid = "https://www.youtube.com/watch?v=05_eHt-46IY&list=PL6GqXsUnxEXJv6DqfIWHUCqw-boUyqnQg"

        tracks_data = YouTubeService.get_playlist_tracks(playlist_url_from_vid)

        # Check tracks data format
        assert isinstance(tracks_data, list)
        assert len(tracks_data) == 13

        for track in tracks_data:
            assert isinstance(track, dict)
            assert isinstance(track.get('platform_id'), str)
            assert isinstance(track.get('platform'), str)
            assert isinstance(track.get('name'), str)
            assert isinstance(track.get('artist'), str)
            assert track.get('album') is None  # YouTube doesn't have album info
            assert isinstance(track.get('download_url'), str)