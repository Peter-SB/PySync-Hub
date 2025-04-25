import { useEffect } from 'react'
import { io } from 'socket.io-client'
import { useQueryClient } from '@tanstack/react-query'
import { backendUrl } from '../config'

/**
 * Hook to listen for playlist updates (e.g download progress) via WebSocket and update the query cache accordingly.
 */
export function useSocketPlaylistUpdates() {
    const queryClient = useQueryClient()

    useEffect(() => {
        const socket = io(backendUrl)
        console.log('Socket connected')

        socket.on('download_status', data => {
            queryClient.setQueryData(['playlists'], old => {
                if (!old) return old
                console.log('Socket message received', old, data)
                return old.map(playlist =>
                    playlist.id === data.id
                        ? {
                            ...playlist,
                            download_status: data.status,
                            download_progress: data.progress != null ? data.progress : playlist.download_progress,
                            downloaded_track_count: data.progress != null
                                ? Math.round((data.progress / 100) * playlist.tracks.length)
                                : playlist.downloaded_track_count,
                        }
                        : playlist
                )
            })
        })

        return () => {
            socket.disconnect()
        }
    }, [queryClient])
}
