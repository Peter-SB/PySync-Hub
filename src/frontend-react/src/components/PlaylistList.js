// src/components/PlaylistList.js
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  DndContext,
  useSensor,
  useSensors,
  PointerSensor
} from '@dnd-kit/core';
import './PlaylistList.css';
import FolderItem from './FolderItem';
import PlaylistItem from './PlaylistItem';
import AddFolderForm from './AddFolderForm';
import InsertionZone from './InsertionZone';
import { backendUrl } from '../config';
import {
  buildTree,
  removeItem,
  insertItemAt,
  findItemById,
  isDescendant
} from '../utils/folderUtils';

function PlaylistList({ playlists, fetchPlaylists, selectedPlaylists, onSelectChange }) {
  const [folders, setFolders] = useState([]);
  const [error, setError] = useState('');
  const [treeData, setTreeData] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [activeDropTarget, setActiveDropTarget] = useState(null);

  // Use pointer sensor with a higher activation constraint to avoid accidental drags
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        tolerance: 5
      }
    })
  );

  // Fetch folders when component mounts
  useEffect(() => {
    const fetchFolders = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/folders`);
        const data = await response.json();

        if (response.ok) {
          setFolders(data.folders || []);
        } else {
          setError(data.error || 'Failed to fetch folders');
        }
      } catch (err) {
        console.error('Error fetching folders:', err);
        setError('Error fetching folders');
      }
    };

    fetchFolders();
  }, []);

  // Build tree whenever folders or playlists change
  useEffect(() => {
    if (folders && playlists) {
      const tree = buildTree(folders, playlists);
      console.log('Tree data:', tree); // Debugging line to check the tree structure
      setTreeData(tree);
    }
  }, [folders, playlists]);

  // When drag starts, keep track of the active id
  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  // When dragging over, if the droppable id indicates an insertion zone, update activeDropTarget
  const handleDragOver = (event) => {
    const { active, over } = event;

    if (over && over.id) {
      if (over.id.includes('-insertion-')) {
        const [parentId, indexStr] = over.id.split('-insertion-');
        const index = parseInt(indexStr, 10);

        // For folders being dragged, check valid drop: can't drop on itself or its descendant
        const activeItem = findItemById(treeData, active.id);

        if (activeItem && activeItem.type === 'folder') {
          if (active.id === parentId || isDescendant(activeItem, parentId)) {
            setActiveDropTarget(null);
            return;
          }
        }

        setActiveDropTarget({ parentId, index });
      } else {
        setActiveDropTarget(null);
      }
    } else {
      setActiveDropTarget(null);
    }
  };

  // When drag ends, if the drop target is an insertion zone, remove and reinsert dropped item at the specified index
  const handleDragEnd = async (event) => {
    const { active, over } = event;

    if (over && over.id && over.id.includes('-insertion-')) { // means its a insertion zone
      const [parentId, indexStr] = over.id.split('-insertion-');
      const index = parseInt(indexStr, 10);

      // Check for invalid drops (folder onto itself or its descendant)
      const activeItem = findItemById(treeData, active.id);
      if (activeItem && activeItem.type === 'folder') {
        if (active.id === parentId || isDescendant(activeItem, parentId)) {
          setActiveDropTarget(null);
          setActiveId(null);
          return;
        }
      }

      // Remove the item from its current position
      const { newTree, removed } = removeItem(treeData, active.id);

      if (removed) {
        // Update the UI optimistically
        const updatedTree = insertItemAt(newTree, parentId, index, removed);
        setTreeData(updatedTree);

        try {
          // Send the frontend tree structure directly to the reorder endpoint
          const response = await fetch(`${backendUrl}/api/folders/reorder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: updatedTree })
          });

          if (!response.ok) {
            throw new Error('Failed to reorder items');
          }
        } catch (err) {
          console.error('Error reordering items:', err);
          setError('Failed to update item position');
          fetchPlaylists(); // Refresh to get the server's current state
        }
      }
    }

    setActiveId(null);
    setActiveDropTarget(null);
  };

  // Handler for folder creation
  const handleFolderAdded = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/folders`);
      const data = await response.json();

      if (response.ok) {
        setFolders(data.folders || []);
      }
    } catch (err) {
      console.error('Error refreshing folders:', err);
    }
  };

  // Look up the active draggable item using activeId
  const activeItem = activeId ? findItemById(treeData, activeId) : null;

  // Render tree recursively starting from the root level
  const renderTree = (items, level = 0) => {
    if (!items || !items.length) return null;

    return (
      <>
        {items.map((item, index) => (
          <React.Fragment key={item.id}>
            {/* Insertion zone before each item */}
            <InsertionZone
              parentId="root"
              index={index}
              activeDropTarget={activeDropTarget}
              indent={level}
            />

            {item.type === 'folder' ? (
              <FolderItem
                item={item}
                level={level}
                activeDropTarget={activeDropTarget}
                activeItem={activeItem}
                fetchPlaylists={fetchPlaylists}
                selectedPlaylists={selectedPlaylists}
                onSelectChange={onSelectChange}
              />
            ) : (
              <PlaylistItem
                playlist={item.playlist}
                fetchPlaylists={fetchPlaylists}
                isSelected={selectedPlaylists.includes(item.playlist.id)}
                onSelectChange={onSelectChange}
                draggable={true}
                id={item.id}
              />
            )}

            {/* Add an insertion zone after the last item */}
            {index === items.length - 1 && (
              <InsertionZone
                parentId="root"
                index={items.length}
                activeDropTarget={activeDropTarget}
                indent={level}
              />
            )}
          </React.Fragment>
        ))}
      </>
    );
  };

  return (
    <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
      <div className="mb-2 p-2 bg-white rounded shadow">
        <AddFolderForm onFolderAdded={handleFolderAdded} setError={setError} />
      </div>

      {error && (
        <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-300 rounded">
          {error}
        </div>
      )}

      <DndContext
        sensors={sensors}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div id="playlist-list">
          {treeData.length ? (
            renderTree(treeData)
          ) : (
            <div className="p-4 text-center text-gray-500 bg-white rounded">
              No playlists added yet. If this is your first time using the app, make sure to read the Help page and set your <Link to="/settings" className="text-blue-500 hover:underline">Settings</Link>.
            </div>
          )}
        </div>
      </DndContext>

      <div className="absolute bottom-0 left-0 right-0 h-2 bg-gradient-to-t from-gray-100 to-transparent pointer-events-none"></div>
    </div>
  );
}

export default PlaylistList;
