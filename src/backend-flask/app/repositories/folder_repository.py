import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Set

from app.extensions import db, socketio
from app.models import Playlist, PlaylistTrack, Track, Folder
from app.utils.db_utils import commit_with_retries

logger = logging.getLogger(__name__)


class FolderRepository:
    @staticmethod
    def get_folder_by_id(folder_id: int) -> Optional[Folder]:
        """Retrieve a folder by its ID."""
        return db.session.query(Folder).get(folder_id)
        
    @staticmethod
    def toggle_folder_disabled(folder_id: int) -> Optional[Dict[str, Any]]:
        """
        Toggle the disabled state of a folder.
        
        :param folder_id: The ID of the folder to toggle
        :returns: Dictionary with folder information or None if folder not found
        """
        folder = FolderRepository.get_folder_by_id(folder_id)
        if not folder:
            return None
            
        # Toggle the disabled state
        new_disabled_state = not folder.disabled
        folder.disabled = new_disabled_state
        
        # Recursively disable/enable children
        FolderRepository.recursively_set_disabled_state(folder, new_disabled_state)
            
        # Apply changes to database
        commit_with_retries(db.session)
        
        return {
            'id': folder.id,
            'name': folder.name,
            'parent_id': folder.parent_id,
            'custom_order': folder.custom_order,
            'created_at': folder.created_at.isoformat() if folder.created_at else None,
            'disabled': folder.disabled
        }
    
    @staticmethod
    def recursively_set_disabled_state(folder: Folder, disabled: bool) -> None:
        """
        Helper method to recursively set the disabled state of all children.
        
        :param folder: The folder whose children to update
        :param disabled: The disabled state to set
        """
        # Update all playlists in this folder
        for playlist in folder.playlists:
            playlist.disabled = disabled
            
        # Update all subfolders
        for subfolder in folder.subfolders:
            subfolder.disabled = disabled
            # Recursively update children of this subfolder
            FolderRepository.recursively_set_disabled_state(subfolder, disabled)
            
    @staticmethod
    def update_folder_disabled_state(folder_id: int, update_state: bool = True) -> Tuple[bool, bool]:
        """
        Check if a folder should be disabled based on its children's state.
        A folder should be disabled if ALL of its children (playlists and subfolders) are disabled.
        
        :param folder_id: The ID of the folder to check
        :param update_state: If True, update the folder's disabled state in the database
        :returns: Tuple containing [ Whether the operation was successful (folder found), The determined disabled state (True = disabled, False = enabled) ]
        """
        folder = FolderRepository.get_folder_by_id(folder_id)
        if not folder:
            return False, False
            
        # Get all children's disabled states
        should_be_disabled = FolderRepository.should_folder_be_disabled(folder)
        
        # Update the database if requested and state differs from current
        if update_state and folder.disabled != should_be_disabled:
            folder.disabled = should_be_disabled
            commit_with_retries(db.session)
            
        return True, should_be_disabled
    
    @staticmethod
    def should_folder_be_disabled(folder: Folder) -> bool:
        """
        Helper method to determine if a folder should be disabled based on its children.
        
        :param folder: The folder to check
        :returns: True if all children are disabled, False if any child is enabled
        """
        # If no children, don't change state
        if not folder.playlists and not folder.subfolders:
            return folder.disabled
            
        # Check if any playlist is enabled
        for playlist in folder.playlists:
            if not playlist.disabled:
                return False
                
        # Check if any subfolder is enabled
        for subfolder in folder.subfolders:
            if not subfolder.disabled:
                return False
            
            # Recursively check subfolder's children
            has_enabled_children = not FolderRepository.should_folder_be_disabled(subfolder)
            if has_enabled_children:
                return False
                
        # If we got here, all children are disabled
        return True

    @staticmethod
    def get_playlists_in_custom_order(enabled_only=True) -> List[Playlist]:
        """
        Retrieve all playlists ordered by custom_order within folders hierarchy.
        """
        ordered_playlists: List[Playlist] = []

        # Fetch root-level folders and playlists
        root_folders = Folder.query.filter_by(parent_id=None).order_by(Folder.custom_order).all()
        root_playlists = Playlist.query.filter_by(folder_id=None).order_by(Playlist.custom_order).all()

        # Combine and sort items by custom_order
        items = []
        for folder in root_folders:
            items.append((folder.custom_order, 'folder', folder))
        for pl in root_playlists:
            items.append((pl.custom_order, 'playlist', pl))

        for _, item_type, item in sorted(items, key=lambda x: x[0]):
            if item_type == 'playlist':
                ordered_playlists.append(item)
            else:
                FolderRepository._traverse_folder(item, ordered_playlists)

        if enabled_only:
            ordered_playlists = [playlist for playlist in ordered_playlists if not playlist.disabled]

        return ordered_playlists

    @staticmethod
    def _traverse_folder(folder: Folder, ordered_playlists: List[Playlist]) -> None:
        """
        Recursively traverse a folder's content and append playlists in custom order.
        """
        items = []
        # Add subfolders and playlists with their custom_order
        for subfolder in folder.subfolders:
            items.append((subfolder.custom_order, 'folder', subfolder))
        for pl in folder.playlists:
            items.append((pl.custom_order, 'playlist', pl))

        for _, item_type, item in sorted(items, key=lambda x: x[0]):
            if item_type == 'playlist':
                ordered_playlists.append(item)
            else:
                FolderRepository._traverse_folder(item, ordered_playlists)
