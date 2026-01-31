from flask import Blueprint

api = Blueprint('api', __name__)

# Temporarily disabled until tracklist feature is complete
# from app.routes import playlists, tracks, export, settings, folders, tracklist
from app.routes import playlists, tracks, export, settings, folders
