import { request } from './client';

export function fetchTracklists() {
    return request('/api/tracklists', {
        method: 'GET',
    });
}

export function fetchTracklistById(id) {
    return request(`/api/tracklists/${id}`, {
        method: 'GET',
    });
}

export function processTracklist(tracklistData) {
    return request('/api/tracklists/add', {
        method: 'POST',
        body: tracklistData,
    });
}

export function saveTracklist(tracklistData) {
    return request('/api/tracklists', {
        method: 'POST',
        body: tracklistData,
    });
}

export function updateTracklist(id, tracklistData) {
    return request(`/api/tracklists/${id}`, {
        method: 'PUT',
        body: tracklistData,
    });
}

export function deleteTracklist(id) {
    return request(`/api/tracklists/${id}`, {
        method: 'DELETE',
    });
}

export function refreshTracklist(id) {
    return request(`/api/tracklists/${id}/refresh`, {
        method: 'POST',
    });
}

export function downloadTracklist(id) {
    return request(`/api/tracklists/${id}/download`, {
        method: 'POST',
    });
}

export function searchTracklistEntry(entryId, limit = 5) {
    return request('/api/tracklists/search-tracklist-entry', {
        method: 'POST',
        body: {
            tracklist_entry_id: entryId,
            limit,
        },
    });
}

export function resolveTrackUrl(entryId, url) {
    return request('/api/tracklists/resolve-track-url', {
        method: 'POST',
        body: {
            tracklist_entry_id: entryId,
            url,
        },
    });
}
