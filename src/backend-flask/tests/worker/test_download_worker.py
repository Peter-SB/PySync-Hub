from app.workers.download_worker import DownloadManager
from app.repositories.playlist_repository import PlaylistRepository
from app.services.download_services.spotify_download_service import SpotifyDownloadService
from app.services.download_services.soundcloud_download_service import SoundcloudDownloadService


class DummyPlaylist:
    def __init__(self, id, platform, name="Dummy Playlist", tracks=None):
        self.id = id
        self.platform = platform
        self.name = name
        self.tracks = tracks or []


class TestDownloadWorker:
    def test_download_worker_nonexistent_playlist(self, app, monkeypatch):
        """
        Test that the download worker simply completes a task when the playlist does not exist.
        """
        manager = DownloadManager(app)
        get_playlist_called = False

        def fake_get_playlist_by_id(playlist_id):
            nonlocal get_playlist_called
            get_playlist_called = True
            return None  # Simulate playlist not found

        monkeypatch.setattr(PlaylistRepository, "get_playlist_by_id", fake_get_playlist_by_id)

        manager.add_to_queue("nonexistent_playlist")
        manager.download_queue.join()

        assert get_playlist_called is True

        manager.shutdown()

    def test_download_worker_spotify(self, app, monkeypatch):
        """
        Test that when a Spotify playlist is enqueued, the SpotifyDownloadService is called.
        """
        dummy_playlist = DummyPlaylist(id="spotify1", platform="spotify", name="Spotify Playlist")
        spotify_called = False

        def fake_spotify_download(playlist, cancellation_flags, quick_sync):
            nonlocal spotify_called
            spotify_called = True

        monkeypatch.setattr(
            PlaylistRepository,
            "get_playlist_by_id",
            lambda playlist_id: dummy_playlist if playlist_id == "spotify1" else None,
        )
        monkeypatch.setattr(SpotifyDownloadService, "download_playlist", fake_spotify_download)

        manager = DownloadManager(app)
        manager.add_to_queue("spotify1")
        manager.download_queue.join()  # Wait until the task is processed

        assert "spotify1" in manager.cancellation_flags
        assert not manager.cancellation_flags["spotify1"].is_set()

        assert spotify_called is True

        manager.shutdown()

