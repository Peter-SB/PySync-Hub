import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Set

from app.extensions import db, socketio
from app.models import Playlist, PlaylistTrack, Track, Folder

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
        db.session.commit()
        
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
            db.session.commit()
            
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
