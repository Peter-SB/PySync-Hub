import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
    togglePlaylist,
    syncPlaylists,
    deletePlaylists,
    exportAll,
    addPlaylist,
    cancelDownload,
    refreshPlaylist
} from '../api/playlists'
import { useGlobalError } from '../contexts/GlobalErrorContext';
import { getParentFolderIds, shouldFolderBeDisabled } from '../utils/folderUtils'

export function useAddPlaylist() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (playlistData) => addPlaylist(playlistData),
        onSettled: () => { qc.invalidateQueries({ queryKey: ['playlists'] }) },
    })
}

export function useTogglePlaylist() {
    const { setError } = useGlobalError();
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ playlistId, disabled }) => togglePlaylist(playlistId, disabled),
        onMutate: async ({ playlistId, disabled }) => {
            // Cancel any in-flight queries
            await qc.cancelQueries({ queryKey: ['playlists'] })
            await qc.cancelQueries({ queryKey: ['folders'] })

            // Save the current state
            const previousPlaylists = qc.getQueryData(['playlists'])
            const previousFolders = qc.getQueryData(['folders'])

            // Find the playlist to toggle
            const playlists = qc.getQueryData(['playlists']) || []
            const playlist = playlists.find(p => p.id === playlistId)

            if (!playlist) return { previousPlaylists, previousFolders }

            // Get all parent folder IDs that need updating
            const folders = qc.getQueryData(['folders']) || []
            const parentFolderIds = playlist.folder_id
                ? getParentFolderIds(folders, playlist.folder_id)
                : [];

            // Optimistically update the playlist
            qc.setQueryData(['playlists'], old =>
                old.map(p => p.id === playlistId ? { ...p, disabled } : p)
            )

            // Optimistically update the folders if we have parent folders
            if (parentFolderIds.length > 0) {
                qc.setQueryData(['folders'], old => {
                    // First create a modified copy of playlists with our toggled playlist
                    const updatedPlaylists = playlists.map(p =>
                        p.id === playlistId ? { ...p, disabled } : p
                    );

                    // Now update each parent folder's disabled state
                    return old.map(folder => {
                        if (parentFolderIds.includes(folder.id)) {
                            // Recalculate if this folder should be disabled based on its children
                            const shouldBeDisabled = shouldFolderBeDisabled(
                                old,
                                updatedPlaylists,
                                folder.id
                            );
                            return { ...folder, disabled: shouldBeDisabled };
                        }
                        return folder;
                    });
                });
            }

            return { previousPlaylists, previousFolders }
        },
        onError: (error, _vars, context) => {
            setError(error);
            qc.setQueryData(['playlists'], context.previousPlaylists);
            qc.setQueryData(['folders'], context.previousFolders);
        },
        onSettled: () => {
            qc.invalidateQueries({ queryKey: ['playlists'] })
            qc.invalidateQueries({ queryKey: ['folders'] })
        }
    })
}

export function useSyncPlaylists() {
    return useMutation({
        mutationFn: (playlistIds = []) => syncPlaylists(playlistIds)
        // no need for query invalidation because websocket will handle updating the ui
    })
}

export function useDeletePlaylists() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (playlistIds) => deletePlaylists(playlistIds),
        onSettled: () => { qc.invalidateQueries(['playlists']) }
    })
}

export function useExportAll() {
    return useMutation({
        mutationFn: exportAll,
    })
}

export function useCancelDownload() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (playlistId) => cancelDownload(playlistId),
        // todo: optimistic ui update
        onSettled: () => { qc.invalidateQueries(['playlists']) }
    })
}

export function useRefreshPlaylist() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (playlistId) => refreshPlaylist(playlistId),
        onSettled: () => {
            qc.invalidateQueries({ queryKey: ['playlists'] })
        }
    })
}