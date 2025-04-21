// src/components/FolderItem.js
import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import InsertionZone from './InsertionZone';
import PlaylistItem from './PlaylistItem';

// FolderItem: renders a folder with its label and its children along with insertion zones.
function FolderItem({ item, level, activeDropTarget, activeItem, fetchPlaylists, selectedPlaylists, onSelectChange }) {
    const { attributes, listeners, setNodeRef: setDraggableRef, transform, transition } =
        useDraggable({ id: item.id });

    const indentStyle = { marginLeft: `${level * 30}px` };
    const draggableStyle = transform ? {
        transform: `translate(${transform.x}px, ${transform.y}px)`,
        transition,
    } : {};

    return (
        <>
            <div
                ref={setDraggableRef}
                style={{ ...indentStyle, ...draggableStyle }}
            // className="cursor-grab select-none"
            >
                <div className="flex items-center p-2 my-1 bg-white rounded border shadow hover:shadow-md">
                    <div
                        {...listeners}
                        {...attributes}
                        className="flex items-center cursor-grab pl-2 pr-4"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                        </svg>
                    </div>
                    <span className="font-medium text-gray-700">{item.title}</span>
                </div>
            </div>

            {/* Render children and insertion zones */}
            <div style={{ paddingLeft: `${0 * 30}px` }}>
                {/* Insertion zone before first child */}
                <InsertionZone
                    parentId={item.id}
                    index={0}
                    activeDropTarget={activeDropTarget}
                    indent={(level + 1)}
                />
                {item.children && item.children.map((child, i) => (
                    <React.Fragment key={child.id}>


                        {child.type === 'folder' ? (
                            <FolderItem
                                item={child}
                                level={level + 1}
                                activeDropTarget={activeDropTarget}
                                activeItem={activeItem}
                                fetchPlaylists={fetchPlaylists}
                                selectedPlaylists={selectedPlaylists}
                                onSelectChange={onSelectChange}
                            />
                        ) : (
                            <PlaylistItem
                                playlist={child.playlist}
                                fetchPlaylists={fetchPlaylists}
                                isSelected={selectedPlaylists.includes(child.playlist.id)}
                                onSelectChange={onSelectChange}
                                style={{
                                    marginLeft: `${(level + 1) * 30}px`,
                                    ...(transform ? {
                                        transform: `translate(${transform.x}px, ${transform.y}px)`,
                                        transition
                                    } : {})
                                }}
                                draggable={true}
                                id={child.id}
                            />
                        )}

                        {/* Insertion zone after each child */}
                        <InsertionZone
                            parentId={item.id}
                            index={i + 1}
                            activeDropTarget={activeDropTarget}
                            indent={(level + 1)}
                        />
                    </React.Fragment>
                ))}

                {/* If no children, still need an insertion zone */}
                {/* {(!item.children || item.children.length === 0) && (
                    <InsertionZone
                        parentId={item.id}
                        index={0}
                        activeDropTarget={activeDropTarget}
                        indent={(level + 1)}
                    />
                )} */}
            </div>
        </>
    );
}

export default FolderItem;