import { useQuery } from '@tanstack/react-query'
import { fetchPlaylists } from '../api/playlists'

export function usePlaylists() {
    return useQuery(
        ['playlists'],
        fetchPlaylists,
        {
            refetchOnWindowFocus: false,
        }
    )
}
