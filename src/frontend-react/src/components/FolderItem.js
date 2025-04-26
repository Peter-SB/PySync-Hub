// src/components/FolderItem.js
import React, { useState, useRef, useEffect } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { motion, AnimatePresence } from 'framer-motion';
import InsertionZone from './InsertionZone';
import PlaylistItem from './PlaylistItem';
import { backendUrl } from '../config';
import { useDeleteFolder, useRenameFolder } from '../hooks/useFolderMutations';
import { useFolders } from '../hooks/useFolders';

// FolderItem: renders a folder with its label and its children along with insertion zones.
function FolderItem({ item, level, activeDropTarget, activeItem, fetchPlaylists, selectedPlaylists, onSelectChange, onPlaylistUpdate }) {
    const [isEditing, setIsEditing] = useState(false);
    const [folderName, setFolderName] = useState(item.title);
    const [isSyncing, setIsSyncing] = useState(false);
    const inputRef = useRef(null);
    const deleteFolderMutation = useDeleteFolder();
    const renameFolderMutation = useRenameFolder();
    const { data: folders = [], isLoading, error } = useFolders();
    const folder = folders.find(f => parseInt(f.id) === parseInt(item.id.replace('folder-', '')));

    const deleteFolder = async (e) => {
        e.stopPropagation();
        deleteFolderMutation.mutateAsync(item.originalId);
    };

    // Calculate if folder is disabled based on all child playlists being disabled
    const isFolderDisabled = () => {
        if (!item.children || item.children.length === 0) return true;

        // Check if all children are disabled
        return item.children.every(child => {
            if (child.type === 'folder') {
                // For folder children, we'd need their state but we don't have it directly
                // For simplicity, let's consider an empty folder as disabled
                return !child.children || child.children.length === 0;
            } else {
                // For playlist children, check if they're disabled
                return child.playlist.disabled;
            }
        });
    };

    const [isDisabled, setIsDisabled] = useState(isFolderDisabled());

    // Update disabled state when children change or when item.children changes
    useEffect(() => {
        setIsDisabled(isFolderDisabled());
    }, [item.children]);

    // Force refresh of the disabled state when any child playlist is toggled
    const forceRefreshDisabledState = () => {
        setIsDisabled(isFolderDisabled());
    };

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

    // Recursively collect all playlist IDs from this folder and its subfolders
    const collectPlaylistIds = (folderItem) => {
        let playlistIds = [];

        if (folderItem.children) {
            folderItem.children.forEach(child => {
                if (child.type === 'folder') {
                    // Recursively collect IDs from subfolders
                    playlistIds = [...playlistIds, ...collectPlaylistIds(child)];
                } else if (child.playlist && !child.playlist.disabled) {
                    // Add this playlist's ID if it's not disabled
                    playlistIds.push(child.playlist.id);
                }
            });
        }

        return playlistIds;
    };

    // Recursively collect ALL playlist IDs from this folder and its subfolders (including disabled ones)
    const collectAllPlaylistIds = (folderItem) => {
        let playlistIds = [];

        if (folderItem.children) {
            folderItem.children.forEach(child => {
                if (child.type === 'folder') {
                    // Recursively collect IDs from subfolders
                    playlistIds = [...playlistIds, ...collectAllPlaylistIds(child)];
                } else if (child.playlist) {
                    // Add this playlist's ID regardless of disabled status
                    playlistIds.push(child.playlist.id);
                }
            });
        }

        return playlistIds;
    };

    // Update playlists recursively in the local state
    const updatePlaylistsInFolder = (folderItem, disabled) => {
        if (folderItem.children) {
            folderItem.children.forEach(child => {
                if (child.type === 'folder') {
                    // Recursively update playlists in subfolders
                    updatePlaylistsInFolder(child, disabled);
                } else if (child.playlist && onPlaylistUpdate) {
                    // Update this playlist in the parent component's state
                    onPlaylistUpdate({
                        ...child.playlist,
                        disabled: disabled
                    });
                }
            });
        }
    };

    // Handle toggle for all playlists in this folder
    const handleToggleClick = async (newState) => {
        // Optimistically update the UI
        setIsDisabled(newState);

        // Immediately update the playlist data in the parent component
        if (onPlaylistUpdate) {
            updatePlaylistsInFolder(item, newState);
        }

        const playlistIds = collectAllPlaylistIds(item);

        if (playlistIds.length === 0) {
            return; // No playlists to toggle
        }

        try {
            // Call the toggle API for all playlists
            const response = await fetch(`${backendUrl}/api/playlists/toggle-multiple`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ playlist_ids: playlistIds, disabled: newState }),
            });

            if (!response.ok) {
                throw new Error('Failed to toggle folder playlists');
            }

            fetchPlaylists();
        } catch (error) {
            console.error('Error toggling folder playlists:', error);
            // Revert the UI update if there was an error
            setIsDisabled(!newState);

            // Revert the parent component's data
            if (onPlaylistUpdate) {
                updatePlaylistsInFolder(item, !newState);
            }
        } finally {
            forceRefreshDisabledState();
        }
    };

    // Handle sync for all playlists in this folder
    const handleFolderSync = async (e) => {
        e.stopPropagation();
        const playlistIds = collectPlaylistIds(item);

        if (playlistIds.length === 0) {
            return; // No playlists to sync
        }

        setIsSyncing(true);
        try {
            const response = await fetch(`${backendUrl}/api/playlists/sync`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ playlist_ids: playlistIds }),
            });

            if (!response.ok) {
                throw new Error('Failed to sync folder playlists');
            }

            fetchPlaylists();
        } catch (error) {
            console.error('Error syncing folder playlists:', error);
        } finally {
            setIsSyncing(false);
        }
    };

    // Handle starting the rename process
    const handleStartRename = (e) => {
        e.stopPropagation();
        setIsEditing(true);
    };

    // Handle saving the renamed folder
    const handleSaveRename = async () => {
        if (!folderName.trim() || folderName === folder.name) {
            setFolderName(folder.name);
            setIsEditing(false);
            return;
        }

        setIsEditing(false);
        renameFolderMutation.mutateAsync({ folderId: item.originalId, newName: folderName });
    };

    // Handle cancelling the rename
    const handleCancelRename = () => {
        setFolderName(folder.name);
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
                className="flex flex-row items-center py-0"
            >
                <div className={`flex items-center p-2 pr-4 my-1 rounded border shadow hover:shadow-md flex-1 ${isDisabled ? 'bg-gray-200' : 'bg-white'}`}>
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
                                // onBlur={handleCancelRename}
                                className="px-2 py-1 border rounded focus:outline-none focus:ring focus:border-blue-300"
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
                            <button
                                onClick={deleteFolder}
                                className="ml-1 text-red-600 hover:text-red-800"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m4-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                            </button>
                        </div>
                    ) : (
                        <>
                            <span
                                className={`font-medium cursor-pointer hover:text-blue-600 flex-grow ${isDisabled ? 'text-gray-500' : 'text-gray-700'}`}
                                onClick={handleStartRename}
                            >
                                {folder.name}
                            </span>
                            {/* <button
                                onMouseDown={(e) => e.stopPropagation()}
                                onClick={handleFolderSync}
                                disabled={isSyncing || isDisabled}
                                className={`ml-2 px-3 py-1 font-medium text-sm bg-gray-100 rounded-lg ${(isSyncing || isDisabled) ? 'opacity-50' : 'hover:bg-gray-200'}`}
                            >
                                {isSyncing ? 'Syncing...' : 'Sync'}
                            </button> */}
                        </>
                    )}
                </div>
                <label htmlFor={`toggle-folder-${item.id}`} className="relative inline-flex items-center cursor-pointer ml-2 mr-10">
                    <input
                        type="checkbox"
                        id={`toggle-folder-${item.id}`}
                        onChange={() => handleToggleClick(!isDisabled)}
                        checked={isDisabled}
                        className="sr-only peer"
                    />
                    <div className="relative w-[35px] h-[21px] bg-gray-400 border border-gray-300 rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:ring-gray-600 disabled:opacity-50 disabled:pointer-events-none
                            peer-checked:bg-gray-100
                            before:inline-block before:w-4 before:h-4 before:bg-white before:rounded-full before:shadow before:transition-all before:ease-in-out before:duration-200
                            before:translate-x-[17px] before:translate-y-[-0.5px] peer-checked:before:translate-x-0">
                    </div>
                </label>
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
                                // layoutId={`item-${item.id}`}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 1 }}
                                transition={{
                                    layout: {
                                        type: "tween",
                                    },
                                    opacity: { duration: 0.2 }
                                }}
                                className="item-container"
                            >
                                {child.type === 'folder' ? (
                                    <FolderItem
                                        item={child}
                                        level={level + 1}
                                        activeDropTarget={activeDropTarget}
                                        activeItem={activeItem}
                                        selectedPlaylists={selectedPlaylists}
                                        onSelectChange={onSelectChange}
                                        onPlaylistUpdate={onPlaylistUpdate}
                                    />
                                ) : (
                                    <PlaylistItem
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
                                        onPlaylistUpdate={onPlaylistUpdate}
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