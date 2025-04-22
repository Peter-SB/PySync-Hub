import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from sqlalchemy import desc
from app.extensions import db
from app.models import Folder, Playlist

# todo: Move other routes to separate blueprints
bp = Blueprint('folders', __name__, url_prefix='/api/folders')
logger = logging.getLogger(__name__)

@bp.route('', methods=['GET'])
def get_folders():
    """Retrieve all folders."""
    try:
        folders = Folder.query.all()
        return jsonify({
            'folders': [
                {
                    'id': folder.id,
                    'name': folder.name,
                    'parent_id': folder.parent_id,
                    'custom_order': folder.custom_order,
                    'created_at': folder.created_at.isoformat() if folder.created_at else None
                }
                for folder in folders
            ]
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving folders: {str(e)}")
        return jsonify({'error': 'Failed to retrieve folders'}), 500

@bp.route('', methods=['POST'])  # todo: make this /create, remember to correct frontend
def create_folder():
    """Create a new folder."""
    try:
        data = request.json
        name = data.get('name')
        parent_id = data.get('parent_id')
        
        if not name:
            return jsonify({'error': 'Folder name is required'}), 400
        
        # If parent folder is specified, make sure it exists
        if parent_id:
            parent = Folder.query.get(parent_id)
            if not parent:
                return jsonify({'error': 'Parent folder not found'}), 404
        
        # Place the new folder at the end
        max_order = db.session.query(db.func.max(Folder.custom_order)).filter(
            Folder.parent_id == parent_id
        ).scalar() or 0
        
        # Create the new folder
        # todo: add to a folder repository
        folder = Folder(
            name=name,
            parent_id=parent_id,
            custom_order=max_order + 1,
            created_at=datetime.utcnow()
        )
        
        db.session.add(folder)
        db.session.commit()
        
        return jsonify({
            'id': folder.id,
            'name': folder.name,
            'parent_id': folder.parent_id,
            'custom_order': folder.custom_order,
            'created_at': folder.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating folder: {str(e)}")
        return jsonify({'error': 'Failed to create folder'}), 500

@bp.route('/<int:folder_id>', methods=['DELETE']) 
def delete_folder(folder_id):
    """Delete a folder and optionally its contents."""
    try:
        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({'error': 'Folder not found'}), 404
        
        # Check if force param is true, which means delete contents too
        force = request.args.get('force', 'false').lower() == 'true'
        
        # Check if folder has contents
        has_playlists = Playlist.query.filter_by(folder_id=folder_id).first() is not None
        has_subfolders = Folder.query.filter_by(parent_id=folder_id).first() is not None
        
        if (has_playlists or has_subfolders) and not force:
            return jsonify({
                'error': 'Folder is not empty. Set force=true to delete it and its contents'
            }), 400
        
        # Update playlists to remove folder assignment
        if force:
            Playlist.query.filter_by(folder_id=folder_id).update({
                'folder_id': folder.parent_id
            })
            
            # Recursively process subfolders
            subfolders = Folder.query.filter_by(parent_id=folder_id).all()
            for subfolder in subfolders:
                subfolder.parent_id = folder.parent_id
                db.session.add(subfolder)
        
        # Delete the folder
        db.session.delete(folder)
        db.session.commit()
        
        return jsonify({'message': 'Folder deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting folder: {str(e)}")
        return jsonify({'error': 'Failed to delete folder'}), 500

@bp.route('/<int:folder_id>', methods=['PUT']) 
def update_folder(folder_id):
    """Update folder name or parent."""
    try:
        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({'error': 'Folder not found'}), 404
        
        data = request.json
        
        # Update name if provided
        if 'name' in data:
            folder.name = data['name']
        
        # Update parent if provided
        if 'parent_id' in data:
            parent_id = data['parent_id']
            
            # Prevent making a folder its own parent
            if parent_id == folder_id:
                return jsonify({'error': 'A folder cannot be its own parent'}), 400
                
            # Check if new parent exists (if not null)
            if parent_id is not None:
                parent = Folder.query.get(parent_id)
                if not parent:
                    return jsonify({'error': 'Parent folder not found'}), 404
                
                # Check for circular references
                current = parent
                while current:
                    if current.id == folder_id:
                        return jsonify({'error': 'Cannot create circular folder reference'}), 400
                    current = current.parent

            folder.parent_id = parent_id
        
        db.session.commit()
        
        return jsonify({
            'id': folder.id,
            'name': folder.name,
            'parent_id': folder.parent_id,
            'custom_order': folder.custom_order,
            'created_at': folder.created_at.isoformat() if folder.created_at else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating folder: {str(e)}")
        return jsonify({'error': 'Failed to update folder'}), 500

@bp.route('/move', methods=['POST'])
def move_folder():
    """Move a folder to a different position or parent."""
    try:
        data = request.json
        folder_id = data.get('id')
        new_parent_id = data.get('parent_id')
        position = data.get('position', 0)
        
        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({'error': 'Folder not found'}), 404
        
        # Prevent circular references when changing parent
        if new_parent_id == folder_id:
            return jsonify({'error': 'A folder cannot be its own parent'}), 400
            
        # Check if new parent exists (if not null)
        if new_parent_id is not None:
            parent = Folder.query.get(new_parent_id)
            if not parent:
                return jsonify({'error': 'Parent folder not found'}), 404
            
            # Check for circular references
            current = parent
            while current:
                if current.id == folder_id:
                    return jsonify({'error': 'Cannot create circular folder reference'}), 400
                if current.parent_id is None:
                    break
                current = current.parent
                
        # Get all sibling folders at the new position
        siblings = Folder.query.filter_by(parent_id=new_parent_id).order_by(Folder.custom_order).all()
        
        # Remove the folder from its current position if it's among the siblings
        if folder.parent_id == new_parent_id:
            siblings = [s for s in siblings if s.id != folder_id]
        
        # Insert the folder at the specified position
        siblings.insert(min(position, len(siblings)), folder)
        
        # todo: move to folder repository
        # Update custom_order for all siblings
        for i, sibling in enumerate(siblings):
            sibling.custom_order = i
            db.session.add(sibling)
        
        # Update the parent_id
        folder.parent_id = new_parent_id
        
        db.session.commit()
        
        return jsonify({'message': 'Folder moved successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error moving folder: {str(e)}")
        return jsonify({'error': 'Failed to move folder'}), 500

@bp.route('/reorder', methods=['POST'])
def reorder_tree():
    """
    Reorder the entire folder and playlist custom_order structure from tree.
    
    Accepts frontend tree format:
    {
        "items": [
            {
                "id": "folder-123", 
                "type": "folder", 
                "originalId": "123",
                "children": [...]
            },
            {
                "id": "playlist-456", 
                "type": "playlist", 
                "originalId": "456",
                "playlist": {...}
            },
            ...
        ]
    }
    """
    try:
        data = request.json
        if not data or 'items' not in data:
            return jsonify({'error': 'Invalid data format, "items" array is required'}), 400
            
        # Begin transaction
        db.session.begin_nested()
        
        # Process the tree structure starting at root level
        process_tree_items(data['items'], parent_id=None)
        
        db.session.commit()
        return jsonify({'message': 'Organization structure updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error reorganizing structure: {str(e)}")
        return jsonify({'error': 'Failed to reorganize structure'}), 500

def process_tree_items(items, parent_id=None):
    """
    Recursively process items in the tree, updating their custom_order values.
    
    :param items: List of items (folders/playlists) to process
    :param parent_id: ID of the parent folder, or None for root level
    """
    for i, item in enumerate(items):
        item_type = item.get('type')
        
        if not item_type:
            continue
            
        if item_type == 'folder':
            # Extract the numeric ID from the frontend format (e.g., "folder-123" -> 123)
            item_id = int(item.get('originalId'))
            
            # Update folder's custom_order and parent
            folder = Folder.query.get(item_id)
            if folder:
                folder.custom_order = i
                folder.parent_id = parent_id
                db.session.add(folder)
                
                # Process children if any
                if 'children' in item and isinstance(item['children'], list):
                    process_tree_items(item['children'], parent_id=item_id)
                    
        elif item_type == 'playlist':
            # Extract the numeric ID from the frontend format (e.g., "playlist-456" -> 456)
            item_id = int(item.get('originalId'))
            
            # Update playlist's custom_order and folder
            playlist = Playlist.query.get(item_id)
            if playlist:
                playlist.custom_order = i
                playlist.folder_id = parent_id
                db.session.add(playlist)
                
    db.session.flush()
