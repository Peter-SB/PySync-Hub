import logging
from flask import Blueprint, render_template, request, Response

from app.repositories.playlist_repository import PlaylistRepository
from app.services.playlists_service import PlaylistService

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
    url_or_id: str = request.form.get('url_or_id', str)
    logger.info(f"Adding playlist: {url_or_id}")

    error = PlaylistService.add_playlists(url_or_id)

    playlists_html = get_playlists()
    if error:
        logging.error(error)
        error_box = render_template('partials/error_box.html', error=error)
        return error_box + playlists_html

    return playlists_html

@main.route('/playlists/update', methods=['POST'])
def update_playlists() -> str:
    selected_ids: list[int] = request.form.getlist('playlist_ids', int)
    PlaylistService.update_playlists(selected_ids)
    return get_playlists()

@main.route('/playlists', methods=['DELETE'])
def delete_playlists() -> str:
    selected_ids: list[int] = request.form.getlist('playlist_ids', int)
    PlaylistService.delete_playlists(selected_ids)
    return get_playlists()
