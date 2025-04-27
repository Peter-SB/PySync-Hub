import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
    togglePlaylist,
    toggleMultiplePlaylists,
    syncPlaylists,
    deletePlaylists,
    exportAll,
    addPlaylist,
    cancelDownload
} from '../api/playlists'
import { useGlobalError } from '../contexts/GlobalErrorContext';

export function useAddPlaylist() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (playlistData) => addPlaylist(playlistData),
        onSuccess: () => { qc.invalidateQueries(['playlists']) },
    })
}

export function useTogglePlaylist() {
    const { setError } = useGlobalError();
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ playlistId, disabled }) => togglePlaylist(playlistId, disabled),
        onMutate: async ({ playlistId, disabled }) => {
            await qc.cancelQueries({ queryKey: ['playlists'] })
            const previous = qc.getQueryData(['playlists'])
            qc.setQueryData(['playlists'], old =>
                old.map(p => p.id === playlistId ? { ...p, disabled } : p)
            )
            return { previous }
        },
        onError: (error, _vars, context) => {
            setError(error);
            qc.setQueryData(['playlists'], context.previous);
        },
        onSettled: () => {
            qc.invalidateQueries({ queryKey: ['playlists'] })
        }
    })
}

export function useToggleMultiplePlaylists() {
    const { setError } = useGlobalError();
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ playlistIds, disabled }) => toggleMultiplePlaylists(playlistIds, disabled),
        onMutate: async ({ playlistIds, disabled }) => {
            await qc.cancelQueries({ queryKey: ['playlists'] })
            const previous = qc.getQueryData(['playlists'])
            qc.setQueryData(['playlists'], old =>
                old.map(p => playlistIds.includes(p.id) ? { ...p, disabled } : p)
            )
            return { previous }
        },
        onError: (error, _vars, context) => {
            setError(error);
            qc.setQueryData(['playlists'], context.previous);
        },
        onSettled: () => {
            qc.invalidateQueries({ queryKey: ['playlists'] })
        }
    })
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

export function useCancelDownload() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (playlistId) => cancelDownload(playlistId),
        // todo: optimistic ui update
        onSuccess: () => { qc.invalidateQueries(['playlists']) }
    })
}