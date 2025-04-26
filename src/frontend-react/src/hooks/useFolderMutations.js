import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
    createFolder,
    renameFolder,
    deleteFolder,
    reorderFolders,
    moveItems
} from '../api/folders'
import { useGlobalError } from '../contexts/GlobalErrorContext'

export function useCreateFolder() {
    const qc = useQueryClient()
    return useMutation(
        {
            mutationFn: ({ name }) => createFolder(name),
            onSettled: () => qc.invalidateQueries(['folders'])
        }
    )
}

export function useRenameFolder() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ folderId, newName }) => renameFolder(folderId, newName),
        onSettled: () => qc.invalidateQueries(['folders']),
    })
}

export function useDeleteFolder() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (folderId) => deleteFolder(folderId),
        onSettled: () => qc.invalidateQueries(['folders'])
    }
    )
}

// export function useReorderFolders() {
//     const { setError } = useGlobalError();
//     const qc = useQueryClient()
//     return useMutation({
//         mutationFn: (items) => reorderFolders(items),

//         onMutate: async (items) => {
//             await qc.cancelQueries({ queryKey: ['folders'] })
//             await qc.cancelQueries({ queryKey: ['playlists'] })

//             const previousFolders = qc.getQueryData(['folders'])
//             const previousPlaylists = qc.getQueryData(['playlists'])

//             // Update folders in the cache
//             qc.setQueryData(['folders'], old => {
//                 if (!old) return old;

//                 // Create a copy of the original folders
//                 const updatedFolders = [...old];

//                 // Update folders that are being reordered
//                 items.forEach(item => {
//                     if (item.type === 'folder') {
//                         // Extract the numeric ID from "folder-X" format
//                         // todo: replace with originalId
//                         const folderId = parseInt(item.id.replace('folder-', ''));
//                         console.log("Folder ID", folderId)

//                         // Find the folder in the cache and update its order
//                         const folderIndex = updatedFolders.findIndex(f => f.id === folderId);
//                         if (folderIndex !== -1) {
//                             updatedFolders[folderIndex] = {
//                                 ...updatedFolders[folderIndex],
//                                 custom_order: item.custom_order
//                             };
//                         }
//                     }
//                 });

//                 return updatedFolders;
//             })

//             // Update playlists in the cache
//             qc.setQueryData(['playlists'], old => {
//                 if (!old) return old;

//                 const updatedPlaylists = [...old];

//                 items.forEach(item => {
//                     if (item.type !== 'folder') {
//                         const playlistIndex = updatedPlaylists.findIndex(p => p.id === item.id);  // todo: replace with originalId
//                         if (playlistIndex !== -1) {
//                             updatedPlaylists[playlistIndex] = {
//                                 ...updatedPlaylists[playlistIndex],
//                                 custom_order: item.custom_order
//                             };
//                         }
//                     }
//                 });

//                 return updatedPlaylists;
//             })

//             return { previousFolders, previousPlaylists }
//         },

//         onError: (error, _vars, context) => {
//             setError(error);
//             qc.setQueryData(['folders'], context.previousFolders)
//             qc.setQueryData(['playlists'], context.previousPlaylists)
//         },

//         onSettled: () => {
//             qc.invalidateQueries({ queryKey: ['folders'] });
//             qc.invalidateQueries({ queryKey: ['playlists'] });
//         }
//     })
// }

export function useMoveItems() {
    const qc = useQueryClient()

    return useMutation({
        mutationFn: (items) => moveItems(items),

        onMutate: async (items) => {
            await qc.cancelQueries({ queryKey: ['folders'] })
            await qc.cancelQueries({ queryKey: ['playlists'] })

            console.log("Moving items", items)

            const previousFolders = qc.getQueryData(['folders'])
            const previousPlaylists = qc.getQueryData(['playlists'])

            console.log("Previous folders", previousFolders)
            console.log("Previous playlists", previousPlaylists)

            // Optimistically update only the changed items
            qc.setQueryData(['folders'], (folders = []) =>
                folders.map(f => {
                    const fl_item = items.find(i => i.type === 'folder' && i.id === f.id)
                    return fl_item
                        ? { ...f, parent_id: fl_item.parent_id, custom_order: fl_item.custom_order }
                        : f
                })
            )
            qc.setQueryData(['playlists'], (pls = []) =>
                pls.map(p => {
                    const pl_item = items.find(i => i.type === 'playlist' && i.id === p.id)
                    return pl_item
                        ? { ...p, folder_id: pl_item.parent_id, custom_order: pl_item.custom_order }
                        : p
                })
            )

            return { previousFolders, previousPlaylists }
        },

        onError: (_err, _ops, context) => {
            qc.setQueryData(['folders'], context.previousFolders)
            qc.setQueryData(['playlists'], context.prevP)
        },

        onSettled: () => {
            qc.invalidateQueries({ queryKey: ['playlists'] })
            qc.invalidateQueries({ queryKey: ['folders'] })
        }
    })
}
