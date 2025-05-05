import logging
import os
import urllib
import xml.etree.ElementTree as ET
from typing import Optional, Union, Any
from xml.dom import minidom
from datetime import datetime

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from app.extensions import db
from app.models import Playlist, Folder, Track
from app.repositories.playlist_repository import PlaylistRepository

logger = logging.getLogger(__name__)

DownloadedTrackType = tuple[int, str]


class ExportItunesXMLService:
    @staticmethod
    def generate_rekordbox_xml_from_db(EXPORT_FOLDER, EXPORT_FILENAME) -> str:
        """
        Generates a Rekordbox XML file reflecting the folder/playlist structure
        while mixing playlists and folders in a custom order.
        """
        # Instantiate the XML library helper
        xml_lib = RekordboxXMLLibrary()

        # Process top-level items (those with no parent folder) using "PySyncDJ" as the root persistent ID
        ExportItunesXMLService._process_container(xml_lib, parent_folder_id=None, parent_persistent_id="PySyncDJ")

        # Save the resulting XML
        xml_lib.save_xml(EXPORT_FOLDER, EXPORT_FILENAME)
        return os.path.join(EXPORT_FOLDER, EXPORT_FILENAME)

    @staticmethod
    def _process_container(xml_lib, parent_folder_id, parent_persistent_id):
        """
        Processes all items (playlists and folders) that have the given parent.
        Both playlists and folders are merged and sorted by their custom order.
        For folders, the method calls itself recursively.
        """
        # Fetch playlists that belong to the current container
        playlists = Playlist.query.filter(
            Playlist.folder_id == parent_folder_id,
            Playlist.disabled == False
        ).all()
        
        # Fetch folders (subfolders) that have this parent
        folders = Folder.query.filter(
            Folder.parent_id == parent_folder_id,
            Folder.disabled == False
        ).all()

        # Merge both lists and sort by the custom_order property
        items = playlists + folders
        items.sort(key=lambda item: item.custom_order)

        # Process each item in the sorted order
        for item in items:
            if isinstance(item, Folder):
                # Generate an XML ID for the folder and form its persistent ID
                folder_xml_id = xml_lib.gen_playlist_id()
                folder_persistent_id = f"folder-{folder_xml_id}"
                folder_info = {
                    "Name": item.name,
                    "Description": " ",
                    "Playlist ID": folder_xml_id,
                    "Playlist Persistent ID": folder_persistent_id,
                    "Parent Persistent ID": parent_persistent_id,
                    "Folder": True
                }
                xml_lib.add_playlist_from_elements(folder_info)

                # Recursively process the subfolder's items
                ExportItunesXMLService._process_container(
                    xml_lib, 
                    parent_folder_id=item.id, 
                    parent_persistent_id=folder_persistent_id
                )

            elif isinstance(item, Playlist):
                # For a playlist, grab the absolute file paths from its tracks
                file_locations = [
                    pt.track.absolute_download_path 
                    for pt in item.tracks 
                    if pt.track and pt.track.download_location
                ]
                
                if not file_locations:
                    continue

                playlist_xml_id = xml_lib.gen_playlist_id()
                
                # Build track entries
                track_entries = []
                track_ids = []
                for file_location in file_locations:
                    if file_location:  # Only add if the path is valid
                        track_id = xml_lib.gen_track_id()
                        track_ids.append(track_id)
                        track_entries.append((track_id, file_location))
                
                # Add the track info to the XML's tracks dictionary
                xml_lib.add_to_all_track(track_entries)

                # Add the playlist info
                playlist_info = {
                    "Name": item.name,
                    "Description": " ",
                    "Playlist ID": playlist_xml_id,
                    "Playlist Persistent ID": f"{playlist_xml_id}",
                    "Parent Persistent ID": parent_persistent_id,
                    "All Items": True,
                    "Playlist Items": [{"Track ID": tid} for tid in track_ids]
                }
                xml_lib.add_playlist_from_elements(playlist_info)


class RekordboxXMLLibrary:
    """
    This class builds an iTunes Music Library XML file to be used by Rekordbox.
    The XML mimics an iTunes library so that users can import their whole PySync DJ
    library using Rekordbox's import iTunes library feature.
    """

    def __init__(self) -> None:
        """
        Initialize the RekordboxXMLLibrary class.
        """
        self.unique_track_id_counter = -1
        self.unique_playlist_id_counter = 1

        self.playlists_array: Optional[ET.Element] = None
        self.all_tracks_dict: Optional[ET.Element] = None
        self.plist: Optional[ET.Element] = None

        self.create_empty_library_xml()

    def gen_track_id(self) -> int:
        """Generate a unique track id."""
        self.unique_track_id_counter += 1
        return self.unique_track_id_counter

    def gen_playlist_id(self) -> int:
        """Generate a unique playlist id."""
        self.unique_playlist_id_counter += 1
        return self.unique_playlist_id_counter

    def create_empty_library_xml(self) -> None:
        # XML declaration and root element setup
        self.plist = ET.Element("plist", version="1.0")

        # Main dictionary element
        main_dict = ET.SubElement(self.plist, "dict")

        # Add "Library Persistent ID" key with an empty string value
        ET.SubElement(main_dict, "key").text = "Library Persistent ID"
        ET.SubElement(main_dict, "string").text = " "  # Needed or Rekordbox won't read the XML

        # All tracks in library dictionary
        ET.SubElement(main_dict, "key").text = "Tracks"
        self.all_tracks_dict = ET.SubElement(main_dict, "dict")

        # Playlists array for adding playlist (or folder) dicts
        ET.SubElement(main_dict, "key").text = "Playlists"
        self.playlists_array = ET.SubElement(main_dict, "array")

        self.add_root_playlist()

    def save_xml(self, EXPORT_FOLDER, EXPORT_FILENAME: str = "PySyncLibrary.xml") -> None:
        # Convert to a pretty XML string
        rough_string = ET.tostring(self.plist, "utf-8")
        reparsed = minidom.parseString(rough_string)
        pretty_xml_str = reparsed.toprettyxml(indent="  ", encoding="UTF-8")

        # Write the doctype manually since ElementTree won't do it for us (needed by Rekordbox)
        doctype = '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
        final_xml_content = doctype + '\n' + pretty_xml_str.decode('utf-8')

        # Save to file based on settings
        file_location = os.path.join(EXPORT_FOLDER,EXPORT_FILENAME)
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "w", encoding="UTF-8") as f:
            f.write(final_xml_content)
        logger.info(f"Exported XML file to {file_location}")

    def add_playlist(self, playlist_name: str, file_locations: list[str], parent_persistent_id: str = "PySyncDJ") -> None:
        """
        Adds playlist information to the playlists element.

        :param playlist_name: Name of the playlist.
        :param file_locations: List of file locations for tracks.
        :param parent_persistent_id: ID of the parent folder.
        """
        track_dict = [(self.gen_track_id(), file_location) for file_location in file_locations]

        self.add_to_all_track(track_dict)

        playlist_id = self.gen_playlist_id()

        playlist_info = {
            "Name": playlist_name,
            "Description": " ",
            "Playlist ID": playlist_id,
            "Playlist Persistent ID": f"{playlist_id}",
            "Parent Persistent ID": parent_persistent_id,
            "All Items": True,
            "Playlist Items": [{"Track ID": track_id} for track_id, _ in track_dict]
        }

        self.add_playlist_from_elements(playlist_info)

    def add_playlist_from_elements(self, playlist_info: dict) -> None:
        playlist_dict = ET.SubElement(self.playlists_array, 'dict')
        for key, value in playlist_info.items():
            ET.SubElement(playlist_dict, 'key').text = key
            if key == "Playlist Items":
                array_element = ET.SubElement(playlist_dict, 'array')
                for item in value:
                    dict_element = ET.SubElement(array_element, 'dict')
                    ET.SubElement(dict_element, 'key').text = 'Track ID'
                    ET.SubElement(dict_element, 'integer').text = str(item['Track ID'])
            elif isinstance(value, bool):
                ET.SubElement(playlist_dict, 'true' if value else 'false')
            else:
                child_type = 'string' if isinstance(value, str) else 'integer'
                ET.SubElement(playlist_dict, child_type).text = str(value)

    def add_to_all_track(self, tracks_dict: list[DownloadedTrackType]) -> None:
        """
        Adds track information to the Tracks element.

        :param tracks_dict: List of tuples (track_id, file_location)
        """
        formatted_tracks = self.format_tracks_dic(tracks_dict)
        if formatted_tracks is None:
            return

        for track_id, details in formatted_tracks.items():
            track_key = ET.SubElement(self.all_tracks_dict, 'key')
            track_key.text = str(track_id)

            track_dict = ET.SubElement(self.all_tracks_dict, 'dict')
            for key, value in details.items():
                ET.SubElement(track_dict, 'key').text = key
                child = ET.SubElement(track_dict, 'string' if key != 'Track ID' else 'integer')
                child.text = str(value)

    def format_tracks_dic(self, downloaded_tracks_dict: list[DownloadedTrackType]) \
            -> Optional[dict[int, dict[str, Union[str, int, Any]]]]:
        """
        Formats the track dictionary ready to be saved in the XML tree.
        """
        formatted_track_dict = {}

        for track_id, file_location in downloaded_tracks_dict:
            file_location = os.path.join(file_location)
            try:
                audio = MP3(file_location, ID3=EasyID3)
                name = audio['title'][0] if 'title' in audio else 'Unknown'
                artist = audio['artist'][0] if 'artist' in audio else 'Unknown'
                album = audio['album'][0] if 'album' in audio else 'Unknown'
                # Optionally, add track length or other data here

                location = f"file://localhost/{urllib.parse.quote(file_location)}"

                formatted_track_dict[track_id] = {
                    "Track ID": track_id,
                    "Name": name,
                    "Artist": artist,
                    "Album": album,
                    "Kind": "MPEG audio file",
                    "Persistent ID": track_id,
                    "Track Type": "File",
                    "Location": location
                }

            except Exception as e:
                logger.error(f"Error reading file {file_location}: {e}")
                return None

        return formatted_track_dict

    def add_root_playlist(self) -> None:
        """
        Add the root "PySync DJ" folder.
        This will group all PySync downloads together for better libray organisation.
        """
        root_folder_elements = [
            ("Name", "string", "PySync Hub"),
            ("Description", "string", " "),
            ("Playlist ID", "integer", "1"),
            ("Playlist Persistent ID", "string", "PySyncDJ"),
            ("All Items", "true", None),
            ("Folder", "true", None)
        ]

        root_playlist = ET.SubElement(self.playlists_array, "dict")
        for key, tag, text in root_folder_elements:
            ET.SubElement(root_playlist, "key").text = key
            child = ET.SubElement(root_playlist, tag)
            if text is not None:
                child.text = text
