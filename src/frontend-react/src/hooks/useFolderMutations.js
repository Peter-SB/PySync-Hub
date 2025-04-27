import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
    createFolder,
    renameFolder,
    deleteFolder,
    reorderFolders,
    moveItems,
    toggleFolder
} from '../api/folders'
import { useGlobalError } from '../contexts/GlobalErrorContext'

export function useCreateFolder() {
    const qc = useQueryClient()
    return useMutation(
        {
            mutationFn: ({ name }) => createFolder(name),
            onSettled: () => qc.invalidateQueries(['folders'])
        }
    )
}

export function useRenameFolder() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ folderId, newName }) => renameFolder(folderId, newName),
        onSettled: () => qc.invalidateQueries(['folders']),
    })
}

export function useDeleteFolder() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (folderId) => deleteFolder(folderId),
        onSettled: () => qc.invalidateQueries(['folders'])
    }
    )
}

export function useToggleFolder() {
    const { setError } = useGlobalError();
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (folderId) => toggleFolder(folderId),
        onMutate: async (folderId) => {
            await qc.cancelQueries({ queryKey: ['folders'] })
            await qc.cancelQueries({ queryKey: ['playlists'] })

            const previousFolders = qc.getQueryData(['folders'])
            const previousPlaylists = qc.getQueryData(['playlists'])

            // Get the current folder to toggle
            const folders = qc.getQueryData(['folders']) || []
            const folderToToggle = folders.find(f => f.id === folderId)

            if (!folderToToggle) return { previousFolders, previousPlaylists }

            // The new state will be the opposite of the current state
            const newDisabledState = !folderToToggle.disabled

            // Get all subfolder IDs recursively that will be affected
            const affectedFolderIds = getSubfolderIds(folders, folderId)
            affectedFolderIds.push(folderId) // Include the parent folder itself

            // Optimistically update folders cache
            qc.setQueryData(['folders'], old => {
                if (!old) return old;
                return old.map(folder => {
                    // Toggle all affected folders
                    if (affectedFolderIds.includes(folder.id)) {
                        return { ...folder, disabled: newDisabledState }
                    }
                    return folder;
                });
            })

            // Optimistically update playlists cache
            qc.setQueryData(['playlists'], old => {
                if (!old) return old;

                return old.map(playlist => {
                    // Update playlists that belong to any of the affected folders
                    if (playlist.folder_id && affectedFolderIds.includes(playlist.folder_id)) {
                        return { ...playlist, disabled: newDisabledState }
                    }
                    return playlist;
                });
            })

            return { previousFolders, previousPlaylists }
        },
        onError: (error, _vars, context) => {
            setError(error);
            qc.setQueryData(['folders'], context.previousFolders);
            qc.setQueryData(['playlists'], context.previousPlaylists);
        },
        onSettled: () => {
            qc.invalidateQueries({ queryKey: ['folders'] })
            qc.invalidateQueries({ queryKey: ['playlists'] })
        }
    })
}

// Helper function to get all subfolder IDs recursively
function getSubfolderIds(folders, parentId) {
    const subfolderIds = []

    // Find immediate children
    const children = folders.filter(f => f.parent_id === parentId)

    // Add their IDs
    children.forEach(child => {
        subfolderIds.push(child.id)
        // Recursively add all descendants
        const descendants = getSubfolderIds(folders, child.id)
        subfolderIds.push(...descendants)
    })

    return subfolderIds
}

export function useMoveItems() {
    const qc = useQueryClient()

    return useMutation({
        mutationFn: (items) => moveItems(items),

        onMutate: async (items) => {
            await qc.cancelQueries({ queryKey: ['folders'] })
            await qc.cancelQueries({ queryKey: ['playlists'] })

            const previousFolders = qc.getQueryData(['folders'])
            const previousPlaylists = qc.getQueryData(['playlists'])

            // Optimistically update only the changed items
            qc.setQueryData(['folders'], (folders = []) =>
                folders.map(f => {
                    const fl_item = items.find(i => i.type === 'folder' && i.id === f.id)
                    return fl_item
                        ? { ...f, parent_id: fl_item.parent_id, custom_order: fl_item.custom_order }
                        : f
                })
            )
            qc.setQueryData(['playlists'], (pls = []) =>
                pls.map(p => {
                    const pl_item = items.find(i => i.type === 'playlist' && i.id === p.id)
                    return pl_item
                        ? { ...p, folder_id: pl_item.parent_id, custom_order: pl_item.custom_order }
                        : p
                })
            )

            return { previousFolders, previousPlaylists }
        },

        onError: (_err, _ops, context) => {
            qc.setQueryData(['folders'], context.previousFolders)
            qc.setQueryData(['playlists'], context.prevP)
        },

        onSettled: () => {
            qc.invalidateQueries({ queryKey: ['playlists'] })
            qc.invalidateQueries({ queryKey: ['folders'] })
        }
    })
}
