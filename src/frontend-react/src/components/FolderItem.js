import React, { useState } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';

function FolderItem({ folder, level, onToggleExpand, isExpanded, children }) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: `folder-${folder.id}`,
    data: { type: 'folder', folder }
  });

  const style = {
    transform: CSS.Translate.toString(transform),
    marginLeft: `${level * 20}px`,
    marginBottom: '4px',
    marginTop: '4px',
    cursor: folder.id !== 'root' ? 'grab' : 'default', // Root folder is not draggable
  };

  const handleClick = (e) => {
    if (folder.id !== 'root') { // Root folder always stays expanded
      e.stopPropagation();
      onToggleExpand(folder.id);
    }
  };

  return (
    <div className="folder-container">
      {/* Folder header */}
      <div
        className={`flex items-center p-2 rounded border shadow transition-shadow ${
          folder.id === 'root' ? 'bg-gray-100' : 'bg-white hover:shadow-md'
        }`}
        style={style}
      >
        {folder.id !== 'root' && (
          <div 
            ref={setNodeRef} 
            {...listeners} 
            {...attributes}
            className="w-6 h-6 mr-2 flex items-center justify-center border border-gray-300 rounded cursor-grab"
            onClick={(e) => e.stopPropagation()}
          >
            ≡
          </div>
        )}
        
        <button 
          onClick={handleClick}
          className="mr-2 focus:outline-none"
        >
          {isExpanded ? '▼' : '▶'}
        </button>
        
        <div className="flex items-center">
          <span className="mr-2">📁</span>
          <span className="font-medium">{folder.name}</span>
        </div>
      </div>
      
      {/* Children (subfolders and playlists) - shown only when expanded */}
      {isExpanded && (
        <div className="ml-4">
          {children}
        </div>
      )}
    </div>
  );
}

export default FolderItem;