from flask import Blueprint

api = Blueprint('api', __name__)

from app.routes import playlists, tracks, export, settings
