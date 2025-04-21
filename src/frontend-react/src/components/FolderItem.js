// src/components/FolderItem.js
import React, { useState, useRef, useEffect } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { motion, AnimatePresence } from 'framer-motion';
import InsertionZone from './InsertionZone';
import PlaylistItem from './PlaylistItem';
import { backendUrl } from '../config';

// FolderItem: renders a folder with its label and its children along with insertion zones.
function FolderItem({ item, level, activeDropTarget, activeItem, fetchPlaylists, selectedPlaylists, onSelectChange }) {
    const [isEditing, setIsEditing] = useState(false);
    const [folderName, setFolderName] = useState(item.title);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const inputRef = useRef(null);

    const { attributes, listeners, setNodeRef: setDraggableRef, transform, transition } =
        useDraggable({ id: item.id });

    const indentStyle = { marginLeft: `${level * 30}px` };
    const draggableStyle = transform ? {
        transform: `translate(${transform.x}px, ${transform.y}px)`,
        transition,
    } : {};

    useEffect(() => {
        // When entering edit mode, focus the input
        if (isEditing && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [isEditing]);

    // Handle starting the rename process
    const handleStartRename = (e) => {
        e.stopPropagation();
        setIsEditing(true);
    };

    // Handle saving the renamed folder
    const handleSaveRename = async () => {
        if (!folderName.trim() || folderName === item.title) {
            setFolderName(item.title);
            setIsEditing(false);
            return;
        }

        setIsSubmitting(true);
        try {
            const response = await fetch(`${backendUrl}/api/folders/${item.originalId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: folderName }),
            });

            if (!response.ok) {
                throw new Error('Failed to rename folder');
            }

            item.title = folderName; // Update the folder title on the frontend
        } catch (error) {
            console.error('Error renaming folder:', error);
            setFolderName(item.title); // Revert on error
        } finally {
            setIsSubmitting(false);
            setIsEditing(false);
        }
    };

    // Handle cancelling the rename
    const handleCancelRename = () => {
        setFolderName(item.title);
        setIsEditing(false);
    };

    // Handle key press events
    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleSaveRename();
        } else if (e.key === 'Escape') {
            handleCancelRename();
        }
    };

    return (
        <>
            <div
                ref={setDraggableRef}
                style={{ ...indentStyle, ...draggableStyle }}
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
                    {isEditing ? (
                        <div className="flex items-center">
                            <input
                                ref={inputRef}
                                type="text"
                                value={folderName}
                                onChange={(e) => setFolderName(e.target.value)}
                                onKeyDown={handleKeyDown}
                                onBlur={handleCancelRename}
                                className="px-2 py-1 border rounded focus:outline-none focus:ring focus:border-blue-300"
                                disabled={isSubmitting}
                            />
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleSaveRename();
                                }}
                                className="ml-2 text-green-600 hover:text-green-800"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </button>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleCancelRename();
                                }}
                                className="ml-1 text-red-600 hover:text-red-800"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    ) : (
                        <span
                            className="font-medium text-gray-700 cursor-pointer hover:text-blue-600"
                            onClick={handleStartRename}
                        >
                            {item.title}
                        </span>
                    )}
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

                <AnimatePresence>
                    {item.children && item.children.map((child, i) => (
                        <React.Fragment key={child.id}>
                            <motion.div
                                layout
                                transition={{ type: "spring", bounce: 0.25 }}
                            >
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
                            </motion.div>

                            {/* Insertion zone after each child */}
                            <InsertionZone
                                parentId={item.id}
                                index={i + 1}
                                activeDropTarget={activeDropTarget}
                                indent={(level + 1)}
                            />
                        </React.Fragment>
                    ))}
                </AnimatePresence>
            </div>
        </>
    );
}

export default FolderItem;