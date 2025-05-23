/**
 * Helper to convert flat lists of folders and playlists into a tree structure
 * 
 * @param {Array} folders - List of folder objects from the API
 * @param {Array} playlists - List of playlist objects from the API
 * @returns {Array} - Tree structure with folders and playlists
 */
export function buildTree(folders, playlists) {
    // Map to track all folders by ID for quick lookup
    const folderMap = new Map();

    // Initialize the root items array (items with no parent)
    const rootItems = [];

    // First pass: Create folder nodes and store in map
    folders.forEach(folder => {
        folderMap.set(folder.id, {
            id: `folder-${folder.id}`,
            type: 'folder',
            title: folder.name,
            originalId: folder.id,
            parent_id: folder.parent_id,
            custom_order: folder.custom_order,
            children: []
        });
    });

    // Second pass: Build the folder hierarchy
    folders.forEach(folder => {
        const folderNode = folderMap.get(folder.id);

        // If folder has a parent, add it to parent's children
        if (folder.parent_id !== null) {
            const parentNode = folderMap.get(folder.parent_id);
            if (parentNode) {
                parentNode.children.push(folderNode);
            }
        } else {
            // If no parent, it's a root item
            rootItems.push(folderNode);
        }
    });

    // Third pass: Add playlists to their folders
    playlists.forEach(playlist => {
        const playlistNode = {
            id: `playlist-${playlist.id}`,
            type: 'playlist',
            title: playlist.name,
            originalId: playlist.id,
            playlist: playlist, // Store the full playlist object
            custom_order: playlist.custom_order
        };

        // If playlist has a folder, add it to that folder's children
        if (playlist.folder_id !== null) {
            const folderNode = folderMap.get(playlist.folder_id);
            if (folderNode) {
                folderNode.children.push(playlistNode);
            } else {
                // If folder not found, add to root
                rootItems.push(playlistNode);
            }
        } else {
            // If no folder, it's a root item
            rootItems.push(playlistNode);
        }
    });

    // Sort all children by custom_order
    const sortByOrder = (a, b) => a.custom_order - b.custom_order;

    // Recursively sort all children
    function sortChildren(items) {
        if (!items || !items.length) return items;

        items.sort(sortByOrder);

        for (const item of items) {
            if (item.children && item.children.length) {
                sortChildren(item.children);
            }
        }

        return items;
    }

    return sortChildren(rootItems);
}

/**
 * Helper to remove an item from the tree
 * 
 * @param {Array} tree - Current tree structure
 * @param {String} id - ID of the item to remove
 * @returns {Object} - New tree and the removed item
 */
export function removeItem(tree, id) {
    let removed = null;
    const filterItems = items =>
        items.filter(item => {
            if (item.id === id) {
                removed = item;
                return false;
            }
            if (item.children) {
                item.children = filterItems(item.children);
            }
            return true;
        });
    const newTree = filterItems([...tree]);
    return { newTree, removed };
}

/**
 * Helper to insert an item into a folder at a given index
 * 
 * @param {Array} tree - Current tree structure
 * @param {String} parentId - ID of the parent to insert into
 * @param {Number} index - Index at which to insert the item
 * @param {Object} item - Item to insert
 * @returns {Array} - Updated tree
 */
export function insertItemAt(tree, parentId, index, item) {
    if (parentId === 'root') {
        // Insert at the root level
        const newTree = [...tree];
        newTree.splice(index, 0, item);
        return newTree;
    }

    const insert = items =>
        items.map(i => {
            if (i.id === parentId) {
                if (!i.children) i.children = [];
                const newChildren = [...i.children];
                newChildren.splice(index, 0, item);
                return { ...i, children: newChildren };
            }
            if (i.children) {
                return { ...i, children: insert(i.children) };
            }
            return i;
        });
    return insert([...tree]);
}

/**
 * Recursively find an item in the tree
 * 
 * @param {Array} items - Tree or subtree to search
 * @param {String} id - ID of the item to find
 * @returns {Object|null} - Found item or null
 */
export function findItemById(items, id) {
    for (let item of items) {
        if (item.id === id) return item;
        if (item.children) {
            const found = findItemById(item.children, id);
            if (found) return found;
        }
    }
    return null;
}

/**
 * Find the parent ID and index of an item in the tree
 * 
 * @param {Array} items - Tree or subtree to search
 * @param {String} id - ID of the item to find
 * @param {String} parentId - ID of the current parent (defaults to 'root')
 * @returns {Object|null} - { parentId, index } if found, otherwise null
 */
export function findParentAndIndex(items, id, parentId = 'root') {
    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.id === id) {
            return { parentId, index: i };
        }
        if (item.children) {
            const result = findParentAndIndex(item.children, id, item.id);
            if (result) return result;
        }
    }
    return null;
}

/**
 * Check if a folder has a certain descendant
 * 
 * @param {Object} folder - Folder to check
 * @param {String} descendantId - ID of the potential descendant
 * @returns {Boolean} - True if descendant is found
 */
export function isDescendant(folder, descendantId) {
    if (!folder.children) return false;
    for (let child of folder.children) {
        if (child.id === descendantId) return true;
        if (child.children && isDescendant(child, descendantId)) return true;
    }
    return false;
}

/**
 * Flatten the tree into a list of nodes for backend
 * 
 * @param {Array} tree - Current tree structure 
 * @returns {Array} - List of nodes to send to backend
 */
export function getFolderOperations(tree) {
    const treeNodes = [];

    function processNode(node, parentId, index) {
        const itemType = node.id.startsWith('folder-') ? 'folder' : 'playlist';
        const itemId = parseInt(node.originalId, 10);

        if (isNaN(itemId)) {
            console.warn(`Invalid ID in node`, node);
            throw new Error(`Invalid ID in node: ${node.id}`);
        }

        treeNodes.push({
            type: itemType,
            id: itemId,
            parent_id: parentId,
            custom_order: index
        });

        if (itemType === 'folder' && Array.isArray(node.children)) {
            node.children.forEach((child, idx) => processNode(child, itemId, idx));
        } else if (itemType === 'playlist' && node.children?.length) {
            console.error('Playlists should not have children:', node);
        }
    }

    tree.forEach((node, index) => processNode(node, null, index));

    return treeNodes;
}

/**
 * Helper function to find all parent folder IDs for a playlist
 * @param {Array} folders - All folders
 * @param {Integer} folderId - The ID of the folder to find parents for
 * @returns 
 */
export function getParentFolderIds(folders, folderId) {
    const parentIds = [];
    let currentFolderId = folderId;

    while (currentFolderId) {
        // Add the current folder ID to the list
        parentIds.push(currentFolderId);

        // Find the folder object
        const folder = folders.find(f => f.id === currentFolderId);

        // Move up to its parent, or break if we're at the root
        currentFolderId = folder ? folder.parent_id : null;
    }

    return parentIds;
}

/**
 * Helper function to check if a folder should be disabled based on its children
 * @param {Array} folders - All folders
 * @param {Array} playlists - All playlists
 * @param {Integer} folderId - The ID of the folder to check
 * @returns - True if the folder should be disabled, false otherwise
 */
export function shouldFolderBeDisabled(folders, playlists, folderId) {
    // Get direct child playlists of this folder
    const childPlaylists = playlists.filter(p => p.folder_id === folderId);

    // Get direct child folders of this folder
    const childFolders = folders.filter(f => f.parent_id === folderId);

    // If there are no children at all, the folder should be disabled
    if (childPlaylists.length === 0 && childFolders.length === 0) {
        return true;
    }

    // Check if all child playlists are disabled
    const allPlaylistsDisabled = childPlaylists.length > 0
        ? childPlaylists.every(p => p.disabled)
        : true;

    // Check if all child folders are disabled (recursive check)
    const allFoldersDisabled = childFolders.length > 0
        ? childFolders.every(f => shouldFolderBeDisabled(folders, playlists, f.id))
        : true;

    // The folder should be disabled if all its children (both playlists and folders) are disabled
    return allPlaylistsDisabled && allFoldersDisabled;
}