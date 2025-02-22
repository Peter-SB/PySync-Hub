import logging
import os

from pyrekordbox.rbxml import RekordboxXml
from flask import Blueprint, render_template, request, jsonify, current_app

from app.extensions import db, socketio
from app.models import Playlist, PlaylistTrack
from app.repositories.playlist_repository import PlaylistRepository
from app.services.export_itunesxml_service import ExportItunesXMLService
from app.services.playlist_manager_service import PlaylistManagerService
from app.services.export_rekorbox_service import RekordboxExportService

logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)


@main.route('/')
def index():
    logger.info("Index page requested")
    return render_template('index.html')


@main.route('/playlists')
def get_playlists() -> str:
    selected_ids: list[int] = request.args.getlist('selected_ids', type=int)

    # Check if the request comes from HTMX polling (requests every second)
    if 'HX-Request' in request.headers:
        logging.getLogger('werkzeug').setLevel(logging.ERROR)  # Suppress access log

    #logger.info("Retrieving playlists. Selected IDs: %s", selected_ids)
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

    playlists = PlaylistRepository.get_playlists_by_ids(selected_ids) if selected_ids else PlaylistRepository.get_all_playlists()
    playlists = [p for p in playlists if not p.disabled]

    for playlist in playlists:
        playlist.download_status = "queued"
        socketio.emit("download_status", {"id": playlist.id, "status": "queued"})

    db.session.commit()


    for playlist in playlists:
        PlaylistManagerService.refresh_playlists([playlist])
        current_app.download_manager.add_to_queue(playlist.id)

    return get_playlists()


@main.route('/playlists', methods=['DELETE'])
def delete_playlists() -> str:
    selected_ids: list[int] = request.form.getlist('playlist_ids', int)
    PlaylistManagerService.delete_playlists(selected_ids)
    return get_playlists()


# @main.route("/download/<int:playlist_id>", methods=["POST"])
# def download_playlist(playlist_id):
#     """Endpoint to queue a playlist for download."""
#     current_app.download_manager.add_to_queue(playlist_id)
#     return jsonify({"message": "Download started", "playlist_id": playlist_id})


@main.route("/download/<int:playlist_id>/cancel", methods=["DELETE"])
def cancel_download(playlist_id):
    current_app.download_manager.cancel_download(playlist_id)
    playlist = PlaylistRepository.get_playlist(playlist_id)
    if playlist:
        playlist.download_status = 'ready'
        db.session.commit()
        socketio.emit("download_status", {"id": playlist.id, "status": "ready"})
    return get_playlists()


@main.route('/playlists/toggle', methods=['POST'])
def toggle_playlist():
    # Get the playlist ID and the desired disabled value from the request
    playlist_id = request.form.get('playlist_id', type=int)
    disabled_value = request.form.get('disabled')
    if playlist_id is None or disabled_value is None:
        return ("Missing parameters", 400)

    playlist = PlaylistRepository.get_playlist(playlist_id)
    if not playlist:
        return ("Playlist not found", 404)

    # Convert the string value ("true"/"false") to a boolean
    playlist.disabled = True if disabled_value.lower() == 'true' else False
    from app.extensions import db
    db.session.commit()

    # Re-render only this playlist item so that the new styling reflects the change
    return render_template('partials/playlist_item.html', playlist=playlist, selected_ids=[])


@main.route('/export', methods=['GET'])
def export_rekordbox():
    """
    Exports the SQL database to a Rekordbox XML file.
    If the file already exists in the export folder, it is served directly.
    Otherwise, it is generated from the database.
    """
    logger.info("Exporting")

    EXPORT_FOLDER = os.path.join(os.getcwd(), 'exports')
    EXPORT_FILENAME = 'rekordbox.xml'

    # Check if the export file exists
    # if not os.path.exists(EXPORT_PATH):
    #     # File does not exist, so generate it
    ExportItunesXMLService.generate_rekordbox_xml_from_db(EXPORT_FOLDER, EXPORT_FILENAME)

    return ""