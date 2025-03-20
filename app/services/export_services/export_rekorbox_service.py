from app.models import Playlist

import os
import urllib
import xml.etree.ElementTree as ET
from typing import Optional, Union, Any
from xml.dom import minidom

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from app.config import Config


class RekordboxExportService:
    @staticmethod
    def generate_rekordbox_xml_from_db():
        """
        Generates a Rekordbox XML file using data from the SQL database.
        If the export folder does not exist, it is created.
        """
        # Instantiate our repository
        playlists = Playlist.query.filter_by(disabled=False).all()

        # Create the base Rekordbox XML structure
        dj_playlists = ET.Element("DJ_PLAYLISTS", Version="1.0.0")
        ET.SubElement(dj_playlists, "PRODUCT", Name="rekordbox", Version="7.0.4", Company="AlphaTheta")
        collection = ET.SubElement(dj_playlists, "COLLECTION", Entries="0")
        playlists_node = ET.SubElement(dj_playlists, "PLAYLISTS")
        root_playlist_node = ET.SubElement(playlists_node, "NODE", Type="0", Name="ROOT", Count="0")

        track_id_counter = 1
        track_id_map = {}  # Map from Track.id to Rekordbox TRACK ID
        total_tracks = 0
        playlist_count = 0

        # Iterate over playlists to build playlist nodes and the collection
        for playlist in playlists:
            playlist_node = ET.SubElement(
                root_playlist_node,
                "NODE",
                Name=playlist.name,
                Type="1",
                KeyType="0",
                Entries="0"  # Will update later
            )
            entries_count = 0

            # For each playlist, iterate its tracks in order
            for pt in playlist.tracks:
                track = pt.track
                # Add the track to the collection only once (avoid duplicates)
                if track.id not in track_id_map:
                    location = "file:///" + track.download_location.replace("\\", "/")
                    location = urllib.parse.quote(location, safe=":/")

                    ET.SubElement(
                        collection,
                        "TRACK",
                        TrackID=str(track_id_counter),
                        Name=track.name,
                        Artist=track.artist,
                        Album=track.album if track.album else "Unknown Album",
                        Location=location
                    )
                    track_id_map[track.id] = track_id_counter
                    track_id_counter += 1
                    total_tracks += 1
                # Reference the track in the current playlist node
                ET.SubElement(playlist_node, "TRACK", Key=str(track_id_map[track.id]))
                entries_count += 1

            # Update playlist node with the number of entries and count this playlist
            playlist_node.set("Entries", str(entries_count))
            playlist_count += 1

        collection.set("Entries", str(total_tracks))
        root_playlist_node.set("Count", str(playlist_count))

        EXPORT_FOLDER = os.path.join(os.getcwd(), Config.EXPORT_FOLDER)
        EXPORT_FILENAME = 'rekordbox.xml'
        EXPORT_PATH = os.path.join(EXPORT_FOLDER, EXPORT_FILENAME)

        # Ensure the export folder exists
        if not os.path.exists(EXPORT_FOLDER):
            os.makedirs(EXPORT_FOLDER)

        # Write the XML to the file
        tree = ET.ElementTree(dj_playlists)
        tree.write(EXPORT_PATH, encoding="UTF-8", xml_declaration=True)
        return EXPORT_PATH

    # @staticmethod
    # def generate_rekordbox_xml_from_db():
    #     def generate_rekordbox_xml_from_db(event_logger) -> str:
    #         """
    #         Generates a Rekordbox XML file using data from the SQL database and the new RekordboxXMLLibrary.
    #         Returns the full path to the generated XML file.
    #         """
    #         # Instantiate repository and fetch playlists
    #         playlists = PlaylistRepository.get_all_active_playlists()
    #
    #         # Instantiate the new RekordboxXMLLibrary.
    #         # (We pass in an event_logger; here we use the Flask app's logger.)
    #         xml_lib = RekordboxXMLLibrary(event_logger)
    #
    #         # Iterate over playlists and add each one to the XML.
    #         # For each playlist, gather the file locations from its tracks.
    #         for playlist in playlists:
    #             file_locations = []
    #             # Assume playlist.tracks is a list of PlaylistTrack objects and each has a .track reference.
    #             for pt in playlist.tracks:
    #                 # Check that the track exists and has a download_location defined.
    #                 if pt.track and pt.track.download_location:
    #                     file_locations.append(pt.track.download_location)
    #             if file_locations:
    #                 xml_lib.add_playlist(playlist.name, file_locations)
    #
    #         # Save the XML file.
    #         # The new library writes the file to a location based on your settings.
    #         xml_filename = "rekordbox.xml"
    #         xml_lib.save_xml(xml_filename)
    #
    #         # Build the full file path from settings.
    #         settings = xml_lib.settings  # SettingsSingleton instance
    #         export_path = os.path.join(settings.dj_library_drive, settings.rekordbox_playlist_folder, xml_filename)
    #         return export_path


class RekordboxXMLLibrary:
    """
    This class builds an iTunes Music Library XML file to be used by Rekordbox.
    The XML mimics an iTunes library so that users can import their whole PySync DJ
    library using Rekordbox's import iTunes library feature.
    """

    def __init__(self, event_logger: 'EventQueueLogger') -> None:
        """
        Initialize the RekordboxXMLLibrary class.
        """
        self.unique_track_id_counter = -1
        self.unique_playlist_id_counter = 1

        self.playlists_array: Optional[ET.Element] = None
        self.all_tracks_dict: Optional[ET.Element] = None
        self.plist: Optional[ET.Element] = None

        self.event_logger = event_logger
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

    def save_xml(self, file_name: str = "PySyncLibrary.xml") -> None:
        # Convert to a pretty XML string
        rough_string = ET.tostring(self.plist, "utf-8")
        reparsed = minidom.parseString(rough_string)
        pretty_xml_str = reparsed.toprettyxml(indent="  ", encoding="UTF-8")

        # Write the doctype manually since ElementTree won't do it for us (needed by Rekordbox)
        doctype = '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
        final_xml_content = doctype + '\n' + pretty_xml_str.decode('utf-8')

        # Save to file based on settings
        file_location = os.path.join(
            self.settings.dj_library_drive,
            self.settings.rekordbox_playlist_folder,
            file_name
        )
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "w", encoding="UTF-8") as f:
            f.write(final_xml_content)

    def add_playlist(self, playlist_name: str, file_locations: list[str]) -> None:
        """
        Adds playlist information to the playlists element.

        :param playlist_name: Name of the playlist.
        :param file_locations: List of file locations for tracks.
        """
        track_dict = [(self.gen_track_id(), file_location) for file_location in file_locations]

        self.add_to_all_track(track_dict)

        playlist_id = self.gen_playlist_id()

        playlist_info = {
            "Name": playlist_name,
            "Description": " ",
            "Playlist ID": playlist_id,
            "Playlist Persistent ID": f"{playlist_id}",
            "Parent Persistent ID": "PySyncDJ",
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

    def add_to_all_track(self, tracks_dict: list[tuple[int, str]]) -> None:
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

    def format_tracks_dic(
            self, downloaded_tracks_dict: list[tuple[int, str]]
    ) -> Optional[dict[int, dict[str, Union[str, int, Any]]]]:
        """
        Formats the track dictionary ready to be saved in the XML tree.
        """
        formatted_track_dict = {}

        for track_id, file_location in downloaded_tracks_dict:
            file_location = os.path.join(self.settings.dj_library_drive, file_location)
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
                print(f"Error reading file {file_location}: {e}")
                return None

        return formatted_track_dict

    def add_root_playlist(self) -> None:
        """
        Add the root "PySync DJ" folder.
        """
        root_folder_elements = [
            ("Name", "string", "PySync DJ"),
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