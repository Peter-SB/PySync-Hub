
import pytest

from app.services.platform_services.youtube_service import YouTubeService


@pytest.mark.no_youtube_mock
@pytest.mark.integration
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


    def test_get_playlist_data_with_ytdlp_removed_track(self):
        """  Test case where a video has been removed from the playlist """

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
            assert isinstance(track.get('album'), str)
            assert isinstance(track.get('download_url'), str)


    def test_get_playlist_tracks_with_ytdlp_removed_track(self):
        """  Test case where a video has been removed from the playlist """

        playlist_url_from_vid = "https://www.youtube.com/watch?v=05_eHt-46IY&list=PL6GqXsUnxEXJv6DqfIWHUCqw-boUyqnQg"

        tracks_data = YouTubeService.get_playlist_tracks(playlist_url_from_vid)

        # Check tracks data format
        assert isinstance(tracks_data, list)
        # assert len(tracks_data) == 14 # May change

        for track in tracks_data:
            assert isinstance(track, dict)
            assert isinstance(track.get('platform_id'), str)
            assert isinstance(track.get('platform'), str)
            assert isinstance(track.get('name'), str)
            assert isinstance(track.get('artist'), (str, type(None)))
            assert isinstance(track.get('album'), str)
            assert isinstance(track.get('download_url'), str)
