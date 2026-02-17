import logging
import os
import urllib
import xml.etree.ElementTree as ET
from typing import Optional, Union, Any
from app.models import Playlist, Folder, Track, Tracklist, TracklistEntry, PlaylistTrack
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

DownloadedTrackType = tuple[int, Track]


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

        # Add tracklists under a dedicated root folder (ignore tracklist folders for now)
        ExportItunesXMLService._add_tracklists_root_folder(xml_lib, parent_persistent_id="PySyncDJ")

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
        playlists = Playlist.query.options(
            selectinload(Playlist.tracks).selectinload(PlaylistTrack.track)
        ).filter(
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
                track_entries = []
                track_ids = []
                for pt in item.tracks:
                    track = pt.track
                    if not track or not track.download_location:
                        continue
                    track_id = xml_lib.gen_track_id()
                    track_ids.append(track_id)
                    track_entries.append((track_id, track))

                if not track_entries:
                    continue

                playlist_xml_id = xml_lib.gen_playlist_id()
                
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

    @staticmethod
    def _add_tracklists_root_folder(xml_lib, parent_persistent_id):
        """
        Adds a root "PySync Hub Tracklists" folder and all tracklists as playlists beneath it.
        Tracklist folders are ignored (flattened).
        """
        tracklists = Tracklist.query.options(
            selectinload(Tracklist.tracklist_entries).selectinload(TracklistEntry.confirmed_track)
        ).filter(
            Tracklist.disabled == False
        ).all()

        tracklists = sorted(tracklists, key=lambda item: (item.custom_order, item.id))

        tracklist_playlists = []
        for tracklist in tracklists:
            tracks = ExportItunesXMLService._tracklist_file_locations(tracklist)
            if tracks:
                tracklist_playlists.append((tracklist, tracks))

        if not tracklist_playlists:
            return

        folder_xml_id = xml_lib.gen_playlist_id()
        folder_persistent_id = "PySyncTracklists"
        folder_info = {
            "Name": "PySync Hub Tracklists",
            "Description": " ",
            "Playlist ID": folder_xml_id,
            "Playlist Persistent ID": folder_persistent_id,
            "Parent Persistent ID": parent_persistent_id,
            "Folder": True
        }
        xml_lib.add_playlist_from_elements(folder_info)

        for tracklist, tracks in tracklist_playlists:
            playlist_xml_id = xml_lib.gen_playlist_id()

            track_entries = []
            track_ids = []
            for track in tracks:
                track_id = xml_lib.gen_track_id()
                track_ids.append(track_id)
                track_entries.append((track_id, track))

            if not track_entries:
                continue

            xml_lib.add_to_all_track(track_entries)

            playlist_info = {
                "Name": tracklist.set_name,
                "Description": " ",
                "Playlist ID": playlist_xml_id,
                "Playlist Persistent ID": f"{playlist_xml_id}",
                "Parent Persistent ID": folder_persistent_id,
                "All Items": True,
                "Playlist Items": [{"Track ID": tid} for tid in track_ids]
            }
            xml_lib.add_playlist_from_elements(playlist_info)

    @staticmethod
    def _tracklist_file_locations(tracklist):
        entries = list(tracklist.tracklist_entries or [])
        entries.sort(
            key=lambda entry: (
                entry.order_index is None,
                entry.order_index if entry.order_index is not None else entry.id
            )
        )

        file_locations = []
        for entry in entries:
            track = entry.confirmed_track
            if not track:
                continue
            if track.download_location:
                file_locations.append(track)

        return file_locations


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
        try:
            ET.indent(self.plist, space="  ")
        except AttributeError:
            pass
        pretty_xml_str = ET.tostring(self.plist, "utf-8")

        # Write the doctype manually since ElementTree won't do it for us (needed by Rekordbox)
        doctype = '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
        final_xml_content = doctype + '\n' + pretty_xml_str.decode('utf-8')

        # Save to file based on settings
        file_location = os.path.join(EXPORT_FOLDER,EXPORT_FILENAME)
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "w", encoding="UTF-8") as f:
            f.write(final_xml_content)
        logger.info(f"Exported XML file to {file_location}")

    def add_playlist(self, playlist_name: str, tracks: list[Track], parent_persistent_id: str = "PySyncDJ") -> None:
        """
        Adds playlist information to the playlists element.

        :param playlist_name: Name of the playlist.
        :param tracks: List of tracks.
        :param parent_persistent_id: ID of the parent folder.
        """
        track_dict = [(self.gen_track_id(), track) for track in tracks]

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

        :param tracks_dict: List of tuples (track_id, track)
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

        for track_id, track in downloaded_tracks_dict:
            absolute_path = track.absolute_download_path
            if not absolute_path:
                continue
            name = track.name or 'Unknown'
            artist = track.artist or 'Unknown'
            album = track.album or 'Unknown'

            normalized_path = absolute_path.replace("\\", "/")
            location = f"file://localhost/{urllib.parse.quote(normalized_path)}"

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
