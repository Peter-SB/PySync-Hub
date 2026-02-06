import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    fetchTracklistById,
    processTracklist,
    saveTracklist,
    updateTracklist,
    deleteTracklist,
    refreshTracklist,
    searchTracklistEntry,
    resolveTrackUrl,
    fetchTracklists,
    downloadTracklist
} from '../api/tracklists';

export function useTracklists() {
    return useQuery({
        queryKey: ['tracklists'],
        queryFn: fetchTracklists,
        refetchOnWindowFocus: false,
    });
}

export function useTracklistById(id) {
    return useQuery({
        queryKey: ['tracklists', id],
        queryFn: () => fetchTracklistById(id),
        enabled: !!id,
        refetchOnWindowFocus: false,
    });
}

export function useProcessTracklist() {
    return useMutation({
        mutationFn: processTracklist,
    });
}

export function useSaveTracklist() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: saveTracklist,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tracklists'] });
        },
    });
}

export function useUpdateTracklist() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, data }) => updateTracklist(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tracklists'] });
        },
    });
}

export function useDeleteTracklist() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: deleteTracklist,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tracklists'] });
        },
    });
}

export function useRefreshTracklist() {
    return useMutation({
        mutationFn: refreshTracklist,
    });
}

export function useDownloadTracklist() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id) => downloadTracklist(id),
        onSuccess: (_data, tracklistId) => {
            queryClient.invalidateQueries({ queryKey: ['tracklists'] });
            queryClient.invalidateQueries({ queryKey: ['tracklists', tracklistId] });
        },
    });
}

export function useSearchTracks() {
    return useMutation({
        mutationFn: ({ entryId, limit }) => searchTracklistEntry(entryId, limit),
    });
}

export function useResolveTrackUrl() {
    return useMutation({
        mutationFn: ({ entryId, url }) => resolveTrackUrl(entryId, url),
    });
}
