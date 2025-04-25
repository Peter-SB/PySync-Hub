import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
    createFolder,
    renameFolder,
    deleteFolder,
    reorderFolders
} from '../api/folders'

export function useCreateFolder() {
    const qc = useQueryClient()
    return useMutation(
        {
            mutationFn: ({ name }) => createFolder(name),

            // onMutate: async ({ name }) => {
            //     console.log("Creating folder", name)
            //     await qc.cancelQueries(['folders'])
            //     const previous = qc.getQueryData(['folders'])
            //     console.log("Previous folders", previous)
            //     qc.setQueryData(['folders'], old => [
            //         ...(old ?? []),
            //         { id: null, name, parentId: null, custom_order:  }
            //     ])
            //     return { previous }
            // },

            // onError: (_err, _vars, context) => {
            //     qc.setQueryData(['folders'], context.previous)
            // },

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

export function useReorderFolders() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (items) => reorderFolders(items),

        onMutate: async (items) => {
            await qc.cancelQueries(['folders'])
            const previous = qc.getQueryData(['folders'])
            qc.setQueryData(['folders'], old => {
                const newOrder = items.map(item => {
                    const folder = old.find(f => f.id === item.id)
                    return { ...folder, custom_order: item.custom_order }
                })
                return [...old.filter(f => !items.some(i => i.id === f.id)), ...newOrder]
            })

            return { previous }
        },

        onError: (_err, _vars, context) => {
            qc.setQueryData(['folders'], context.previous)
        },

        onSettled: () => {
            qc.invalidateQueries(['folders']);
            //qc.invalidateQueries(['playlists']);
        }
    }
    )
}
