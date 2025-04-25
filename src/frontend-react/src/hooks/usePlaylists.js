import { useQuery } from '@tanstack/react-query'
import { fetchPlaylists } from '../api/playlists'

export function usePlaylists() {
    return useQuery({
        queryKey: ['playlists'],
        queryFn: fetchPlaylists,
        refetchOnWindowFocus: false,
    })
}
