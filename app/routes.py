import logging
from flask import Blueprint, render_template, request, jsonify, current_app

from app.repositories.playlist_repository import PlaylistRepository
from app.services.playlist_manager_service import PlaylistManagerService


logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)

@main.route('/')
def index():
    logger.info("Index page requested")
    return render_template('index.html')


@main.route('/playlists')
def get_playlists() -> str:
    selected_ids: list[int] = request.args.getlist('selected_ids', type=int)
    logger.info("Retrieving playlists. Selected IDs: %s", selected_ids)
    playlists = PlaylistRepository.get_all_playlists()
    return render_template('partials/playlist_list.html', playlists=playlists, selected_ids=selected_ids)


@main.route('/playlists', methods=['POST'])
def add_playlist() -> str:
    url_or_id: str = request.form.get('url_or_id', '')
    logger.info(f"Adding playlist: {url_or_id}")

    error = PlaylistManagerService.add_playlists(url_or_id)

    playlists_html = get_playlists()
    if error:
        error_box = render_template('partials/error_box.html', error=error)
        return error_box + playlists_html

    return playlists_html


@main.route('/playlists/refresh', methods=['POST'])
def refresh_playlists() -> str:
    logger.info("Refreshing Playlists")

    selected_ids: list[int] = request.form.getlist('playlist_ids', int)

    PlaylistManagerService.refresh_playlists(selected_ids)
    current_app.download_manager.add_to_queue(selected_ids[0])

    return get_playlists()


@main.route('/playlists', methods=['DELETE'])
def delete_playlists() -> str:
    selected_ids: list[int] = request.form.getlist('playlist_ids', int)
    PlaylistManagerService.delete_playlists(selected_ids)
    return get_playlists()

@main.route("/download/<int:playlist_id>", methods=["POST"])
def download_playlist(playlist_id):
    """Endpoint to queue a playlist for download."""
    current_app.download_manager.add_to_queue(playlist_id)
    return jsonify({"message": "Download started", "playlist_id": playlist_id})

@main.route("/download/cancel/<int:playlist_id>", methods=["POST"])
def cancel_download(playlist_id):
    current_app.download_manager.cancel_download(playlist_id)
    return jsonify({"message": "Download canceled", "playlist_id": playlist_id})