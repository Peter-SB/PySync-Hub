from dataclasses import dataclass
import logging
import os
import time
from typing import Optional

import yaml
from flask import Blueprint, request, jsonify, current_app

from app.extensions import db, socketio
from app.models import Track
from app.repositories.playlist_repository import PlaylistRepository
from app.routes import api
from app.services.export_services.export_itunesxml_service import ExportItunesXMLService
from app.services.playlist_manager_service import PlaylistManagerService
from app.utils.file_download_utils import FileDownloadUtils
from app.utils.db_utils import commit_with_retries
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class TracklistEntry:
    full_entry: str
    name: str
    artist: str
    version: Optional[str]
    predicted_tracks: Optional[tuple[Track, int]]  # (Track, confidence_score)
    predicted_track_id: Optional[int]
    confirmed_track_id: Optional[int]
    favourite: bool = False

@dataclass
class Tracklist:
    set_name: str
    artist: Optional[str] 
    tracklist_string: str
    tracklist_entries: list[TracklistEntry]
    rating: Optional[int]


@api.route('/api/tracklists', methods=['GET'])
def get_tracklists():
    pass

@api.route('/api/tracklists', methods=['POST'])
def update_tracklist():    
    """ Add or Update. Take a tracklist string and parse it into a list of tracklist_entries"""
    # 1. Take a tracklist string from the request
    # 2. Use TracklistImportService to pass the string and parse it into tracklist entries
    
    # Return to UI the list of tracklist entries and their predicted track matches for the user to confirm
    
    pass