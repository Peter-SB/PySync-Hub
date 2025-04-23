import { request } from './client';

export function fetchFolders() {
    return request('/api/folders');
}

export function createFolder(name, parentId = null) {
    return request('/api/folders', {
        method: 'POST',
        body: { name, parentId },
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
