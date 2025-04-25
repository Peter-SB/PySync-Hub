import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
    togglePlaylist,
    toggleMultiplePlaylists,
    syncPlaylists,
    deletePlaylists,
    exportAll,
    addPlaylist
} from '../api/playlists'

export function useAddPlaylist() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (playlistData) => addPlaylist(playlistData),
        onSuccess: () => { qc.invalidateQueries(['playlists']) },
    })
}

export function useTogglePlaylist() {
    const qc = useQueryClient()
    return useMutation(
        ({ playlistId, disabled }) => togglePlaylist(playlistId, disabled),
        {
            onMutate: async ({ playlistId, disabled }) => {
                await qc.cancelQueries(['playlists'])
                const previous = qc.getQueryData(['playlists'])
                qc.setQueryData(['playlists'], old =>
                    old.map(p => p.id === playlistId ? { ...p, disabled } : p)
                )
                return { previous }
            },

            onError: (_err, _vars, context) => {
                qc.setQueryData(['playlists'], context.previous)
            },

            onSettled: () => {
                qc.invalidateQueries(['playlists'])
            }
        }
    )
}

export function useSyncPlaylists() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (playlistIds = []) => syncPlaylists(playlistIds),
        onSuccess: () => { qc.invalidateQueries(['playlists']) }
    })
}

export function useDeletePlaylists() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (playlistIds) => deletePlaylists(playlistIds),
        onSuccess: () => { qc.invalidateQueries(['playlists']) }
    })
}

export function useExportAll() {
    return useMutation({
        mutationFn: exportAll,
    })
}