import { request } from './client';

export function fetchFolders() {
    console.log('fetching folders...');
    return request('/api/folders', {
        method: 'GET',
    });
}

export function createFolder(name) {
    return request('/api/folders', {
        method: 'POST',
        body: { name },
    });
}

export function renameFolder(folderId, newName) {
    return request(`/api/folders/${folderId}`, {
        method: 'PUT',
        body: { name: newName },
    });
}

export function deleteFolder(folderId) {
    return request(`/api/folders/${folderId}`, {
        method: 'DELETE',
    });
}

export function reorderFolders(items) {
    return request('/api/folders/reorder', {
        method: 'POST',
        body: { items },
    });
}

export function moveItems(items) {
    return request('/api/folders/move-items', {
        method: 'POST',
        body: { items },
    });
}
