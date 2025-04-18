import React, { useState, useEffect, useMemo } from 'react';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
} from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import PlaylistItem from './PlaylistItem';
import FolderItem from './FolderItem';
import { backendUrl } from '../config';

// InsertionZone component: provides droppable area between items
function InsertionZone({ parentId, index, activeDropTarget, indent }) {
  const { setNodeRef, isOver } = useDroppable({
    id: `${parentId}-insertion-${index}`,
  });

  // Highlight when this zone is the current drop target
  const isActive = isOver && activeDropTarget &&
    activeDropTarget.parentId === parentId &&
    activeDropTarget.index === index;

  return (
    <div
      ref={setNodeRef}
      className="h-[2px] my-[2px]"
      style={{
        backgroundColor: isActive ? 'blue' : 'transparent',
        marginLeft: `${indent}px`,
      }}
    />
  );
}

function FolderManager({ playlists, fetchPlaylists, selectedPlaylists, onSelectChange }) {
  // State for folder/playlist structure
  const [items, setItems] = useState([]);
  // State for expanded/collapsed folders
  const [expandedFolders, setExpandedFolders] = useState({});
  // State for drag and drop operations
  const [activeId, setActiveId] = useState(null);
  const [activeDropTarget, setActiveDropTarget] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5, // 5px of movement before drag starts
      },
    })
  );

  // Fetch folder structure
  useEffect(() => {
    const fetchFolders = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(`${backendUrl}/api/folders`);
        if (response.ok) {
          const data = await response.json();
          
          // Transform data to our tree structure with folders and playlists
          const rootFolder = {
            id: 'root',
            name: 'All Playlists',
            type: 'folder',
            children: generateItemTree(data.folders, playlists, null)
          };

          // Add ungrouped playlists at the root level
          const ungroupedPlaylists = playlists.filter(playlist => !playlist.folder_id);
          ungroupedPlaylists.forEach(playlist => {
            rootFolder.children.push({
              ...playlist,
              type: 'playlist'
            });
          });

          setItems([rootFolder]);
          
          // Set all folders to be expanded by default
          const expanded = {};
          expanded['root'] = true;
          data.folders.forEach(folder => {
            expanded[folder.id] = true;
          });
          setExpandedFolders(expanded);
        } else {
          console.error('Failed to fetch folders');
          
          // If API fails, fallback to flat list of playlists
          const rootFolder = {
            id: 'root',
            name: 'All Playlists',
            type: 'folder',
            children: playlists.map(p => ({ ...p, type: 'playlist' }))
          };
          setItems([rootFolder]);
          setExpandedFolders({ root: true });
        }
      } catch (error) {
        console.error('Error fetching folders:', error);
        
        // Same fallback as above
        const rootFolder = {
          id: 'root',
          name: 'All Playlists',
          type: 'folder',
          children: playlists.map(p => ({ ...p, type: 'playlist' }))
        };
        setItems([rootFolder]);
        setExpandedFolders({ root: true });
      } finally {
        setIsLoading(false);
      }
    };

    fetchFolders();
  }, [playlists]);

  // Helper to generate a tree from flat folders and playlists arrays
  const generateItemTree = (folders, playlists, parentId) => {
    const result = [];
    
    // Add folders that have this parent
    const childFolders = folders.filter(f => f.parent_id === parentId);
    childFolders.sort((a, b) => a.custom_order - b.custom_order);
    
    childFolders.forEach(folder => {
      const children = generateItemTree(folders, playlists, folder.id);
      
      // Add playlists that belong to this folder
      const folderPlaylists = playlists
        .filter(p => p.folder_id === folder.id)
        .sort((a, b) => a.custom_order - b.custom_order)
        .map(p => ({ ...p, type: 'playlist' }));
      
      result.push({
        ...folder,
        type: 'folder',
        children: [...children, ...folderPlaylists]
      });
    });
    
    return result;
  };

  // Toggle folder expansion state
  const handleToggleExpand = (folderId) => {
    setExpandedFolders(prev => ({
      ...prev,
      [folderId]: !prev[folderId]
    }));
  };

  // Handle drag start
  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  // When dragging over an insertion zone, update activeDropTarget
  const handleDragOver = (event) => {
    const { active, over } = event;
    
    if (over && over.id) {
      if (over.id.includes('-insertion-')) {
        const [parentId, indexStr] = over.id.split('-insertion-');
        const index = parseInt(indexStr, 10);
        
        // Find the active item in the tree
        const activeItem = findItemById(active.id.toString());
        
        // Check if the dropzone is valid (prevent dropping a folder into itself)
        if (activeItem && activeItem.type === 'folder') {
          // Extract just the ID part from the activeId (removing 'folder-' prefix)
          const activeIdRaw = active.id.toString().replace('folder-', '');
          
          // Don't allow dropping a folder into itself or its descendants
          if (activeIdRaw === parentId || isDescendant(activeItem, parentId)) {
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

  // On drag end, update the data structure with the new arrangement
  const handleDragEnd = async (event) => {
    const { active, over } = event;
    
    if (over && over.id && over.id.includes('-insertion-')) {
      const [parentId, indexStr] = over.id.split('-insertion-');
      const index = parseInt(indexStr, 10);
      
      // Get the item's actual ID (strip the 'folder-' or 'playlist-' prefix)
      const activeIdRaw = active.id.toString()
        .replace('folder-', '')
        .replace('playlist-', '');
        
      const activeItemType = active.id.toString().startsWith('folder-') ? 'folder' : 'playlist';
      
      // API call to update the item's parent and position
      try {
        const response = await fetch(`${backendUrl}/api/${activeItemType}s/move`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            id: activeIdRaw,
            parent_id: parentId === 'root' ? null : parentId,
            position: index
          }),
        });
        
        if (!response.ok) {
          console.error(`Failed to move ${activeItemType}`);
        }
        
        // Refresh the playlists and folders
        fetchPlaylists();
      } catch (error) {
        console.error(`Error moving ${activeItemType}:`, error);
      }
    }
    
    setActiveId(null);
    setActiveDropTarget(null);
  };

  // Helpers for traversing the item tree
  
  // Find an item by its ID in the item tree
  const findItemById = (id) => {
    const findInItems = (items) => {
      for (const item of items) {
        // Check if IDs match (accounting for type prefixes)
        const itemId = `${item.type}-${item.id}`;
        if (itemId === id) return item;
        
        // Check children if this is a folder
        if (item.children) {
          const found = findInItems(item.children);
          if (found) return found;
        }
      }
      return null;
    };
    
    return findInItems(items);
  };

  // Check if a folder has a specific descendant
  const isDescendant = (folder, descendantId) => {
    if (!folder.children) return false;
    
    for (const child of folder.children) {
      if (child.id === descendantId) return true;
      if (child.type === 'folder' && isDescendant(child, descendantId)) return true;
    }
    
    return false;
  };

  // Render the tree recursively
  const renderItemTree = (itemList, level = 0) => {
    if (!itemList || itemList.length === 0) return null;
    
    return (
      <>
        {itemList.map((item, i) => (
          <React.Fragment key={item.id}>
            <InsertionZone
              parentId={item.id}
              index={0}
              activeDropTarget={activeDropTarget}
              indent={(level + 1) * 20}
            />
            
            {item.type === 'folder' ? (
              <FolderItem
                folder={item}
                level={level}
                onToggleExpand={handleToggleExpand}
                isExpanded={expandedFolders[item.id] !== false} // Default to true if undefined
              >
                {item.children && expandedFolders[item.id] !== false && 
                  renderItemTree(item.children, level + 1)
                }
              </FolderItem>
            ) : (
              <PlaylistItem
                playlist={item}
                fetchPlaylists={fetchPlaylists}
                isSelected={selectedPlaylists.includes(item.id)}
                onSelectChange={onSelectChange}
                level={level}
              />
            )}
            
            <InsertionZone
              parentId={item.id}
              index={i + 1}
              activeDropTarget={activeDropTarget}
              indent={(level + 1) * 20}
            />
          </React.Fragment>
        ))}
      </>
    );
  };

  // Overlay content when dragging
  const activeItem = activeId ? findItemById(activeId) : null;
  
  // Loading state
  if (isLoading) {
    return <div className="p-4 text-center">Loading playlist structure...</div>;
  }

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="playlist-folder-manager">
        {renderItemTree(items)}
      </div>

      <DragOverlay>
        {activeItem && (
          <div className="p-2 bg-gray-100 border border-gray-300 rounded shadow-lg">
            {activeItem.type === 'folder' ? (
              <div className="flex items-center">
                <span className="mr-2">📁</span>
                <span>{activeItem.name}</span>
              </div>
            ) : (
              <div className="flex items-center">
                <span className="mr-2">🎵</span>
                <span>{activeItem.name}</span>
              </div>
            )}
          </div>
        )}
      </DragOverlay>
    </DndContext>
  );
}

export default FolderManager;