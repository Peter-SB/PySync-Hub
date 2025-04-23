import { request } from './client';

export function fetchPlaylists() {
    return request('/api/playlists', {
        method: 'GET',
    });
}

export function syncPlaylists(playlistIds = []) {
    return request('/api/playlists/sync', {
        method: 'POST',
        body: { playlist_ids: playlistIds },
    });
}

export function togglePlaylist(playlistId, disabled) {
    return request('/api/playlists/toggle', {
        method: 'POST',
        body: { playlist_id: playlistId, disabled },
    });
}

export function toggleMultiplePlaylists(playlistIds, disabled) {
    return request('/api/playlists/toggle-multiple', {
        method: 'POST',
        body: { playlist_ids: playlistIds, disabled },
    });
}

export function deletePlaylists(playlistIds) {
    return request('/api/playlists', {
        method: 'DELETE',
        body: { playlist_ids: playlistIds },
    });
}
