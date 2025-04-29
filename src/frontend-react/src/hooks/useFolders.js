import { useQuery } from '@tanstack/react-query'
import { fetchFolders } from '../api/folders'

export function useFolders() {
    return useQuery({
        queryKey: ['folders'],
        queryFn: fetchFolders,
        refetchOnWindowFocus: false,
    })
}