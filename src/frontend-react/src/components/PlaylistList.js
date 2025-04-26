// src/components/PlaylistList.js
import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  DndContext,
  useSensor,
  useSensors,
  PointerSensor
} from '@dnd-kit/core';
import { motion, AnimatePresence } from 'framer-motion';
import FolderItem from './FolderItem'; import PlaylistItem from './PlaylistItem';
import './CustomScrollbar.css';
import './PlaylistList.css';
import InsertionZone from './InsertionZone';
import {
  buildTree,
  removeItem,
  insertItemAt,
  findItemById,
  isDescendant,
  findParentAndIndex,
  getFolderOperations as flattenTreeItems
} from '../utils/folderUtils';
import { useFolders } from '../hooks/useFolders';
import { useCreateFolder, useMoveItems } from '../hooks/useFolderMutations';
import { usePlaylists } from '../hooks/usePlaylists';

function PlaylistList({ selectedPlaylists, onSelectChange }) {
  const [activeId, setActiveId] = useState(null);
  const [activeDropTarget, setActiveDropTarget] = useState(null);
  const [treeData, setTreeData] = useState([]);

  const { data: folders = [] } = useFolders();
  const { data: playlists = [] } = usePlaylists();
  const createFolderMutation = useCreateFolder();
  const moveItemsMutation = useMoveItems();

  // Add folder function
  const addFolder = () => {
    createFolderMutation.mutateAsync({ name: `Folder ${folders.length + 1}` });
  };

  // Memoize the folder and playlist. 
  // Using just keys and order to avoid unnecessary tree structure re-renders when only data (e.g playlist progress) changes   
  const folderKeys = useMemo(() =>

    JSON.stringify(folders.map(f => [f.id, f.parent_id, f.custom_order])),
    [folders]
  );

  const playlistKeys = useMemo(() =>
    JSON.stringify(playlists.map(p => [p.id, p.folder_id, p.custom_order])),
    [playlists]
  );

  // Memoize the tree building operation based on structure changes
  const memoizedTreeData = useMemo(() => {
    console.log('Rebuilding tree data...');
    return buildTree(folders, playlists);
  }, [folderKeys, playlistKeys]);

  // Update state when memoized tree data changes
  useEffect(() => {
    setTreeData(memoizedTreeData);
  }, [memoizedTreeData]);

  // ------------------------------------
  //    Dnd-kit drag and drop handlers
  // ------------------------------------

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        tolerance: 5
      }
    })
  );

  // When drag starts, keep track of the active id
  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  // Look up the active draggable item using activeId
  const activeItem = activeId ? findItemById(treeData, activeId) : null;

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

      // Determine original position to adjust index if moving within same parent to avoid index shift bug
      const origin = findParentAndIndex(treeData, active.id);
      let adjustedIndex = index;
      if (origin && origin.parentId === parentId && origin.index < index) {
        adjustedIndex = index - 1;
      }


      // Update tree and the backend
      const { newTree, removed } = removeItem(JSON.parse(JSON.stringify(treeData)), active.id); // Deep clone to avoid mutating state directly
      if (removed) {
        const updatedTree = insertItemAt(newTree, parentId, adjustedIndex, removed);
        await handleUpdateTree(treeData, updatedTree);
      } else {
        console.error("Item not found in the tree:", active.id);
      }
    }

    setActiveId(null);
    setActiveDropTarget(null);
  };

  // Handle updating the tree by comparing the old and new tree structures then sending the changes to the backend 
  const handleUpdateTree = async (treeData, updatedTree) => {
    // Flatten old & new
    const oldOps = flattenTreeItems(treeData);
    const newOps = flattenTreeItems(updatedTree);

    // Get changed nodes 
    const changed = newOps.filter(n => {
      const o = oldOps.find(x => x.type === n.type && x.id === n.id);
      return !o || o.parent_id !== n.parent_id || o.custom_order !== n.custom_order;
    });

    if (changed.length) {
      await moveItemsMutation.mutateAsync(changed);
    }

    // Reset dnd state
    setActiveId(null);
    setActiveDropTarget(null);
  }

  // Render tree recursively starting from the root level
  const renderTree = (items, level = 0) => {
    if (!items || !items.length) return null;

    return (
      <AnimatePresence>
        {items.map((item, index) => (
          <React.Fragment key={item.id}>
            {/* Insertion zone before each item */}
            <InsertionZone
              parentId="root"
              index={index}
              activeDropTarget={activeDropTarget}
              indent={level}
            />

            <motion.div
              layout
              //layoutId={`item-${item.id}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 1 }}
              transition={{
                layout: {
                  type: "tween",
                },
                opacity: { duration: 0.2 }
              }}
              // style={{ height: activeId === item.id ? 0 : 'auto' }}  // Makes the moved item disappear from the list while dragging, removed because of visual bugs
              className="item-container"
            >
              {item.type === 'folder' ? (
                <FolderItem
                  item={item}
                  level={level}
                  activeDropTarget={activeDropTarget}
                  activeItem={activeItem}
                  selectedPlaylists={selectedPlaylists}
                  onSelectChange={onSelectChange}
                />
              ) : (
                <PlaylistItem
                  id={item.id}
                  isSelected={selectedPlaylists.includes(item.playlist.id)}
                  onSelectChange={onSelectChange}
                  draggable={true}
                />
              )}
            </motion.div>

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
      </AnimatePresence>
    );
  };

  return (
    <div id="playlist-list" className="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
      <DndContext
        sensors={sensors}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        {treeData.length ? (
          renderTree(treeData)
        ) : (
          <div className="p-4 text-center text-gray-500 bg-white rounded">
            No playlists added yet. If this is your first time using the app, make sure to read the Help page and set your <Link to="/settings" className="text-blue-500 hover:underline">Settings</Link>.
          </div>
        )}
      </DndContext>
      <div className="flex justify-center mt-4 mb-6">
        <button
          onClick={addFolder}
          className="p-2 rounded-full bg-white border hover:bg-gray-100 text-white shadow-lg"
        >
          <img src="./icons/add-folder.png" alt="Add Folder" className="w-8 h-8" />
        </button>
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-2 bg-gradient-to-t from-gray-100 to-transparent pointer-events-none"></div>
    </div >
  );
}

export default PlaylistList;
