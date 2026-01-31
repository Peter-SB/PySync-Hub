import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    fetchTracklists,
    fetchTracklistById,
    processTracklist,
    saveTracklist,
    updateTracklist,
    deleteTracklist
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
