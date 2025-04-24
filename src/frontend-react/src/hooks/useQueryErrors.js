import { useQueryClient } from '@tanstack/react-query';


export function useQueryErrors() {
    const queryClient = useQueryClient();

    const queries = queryClient.getQueryCache().getAll();

    const errorQuery = queries.find(query => query.state.error);

    const errorMessage = errorQuery
        ? errorQuery.state.error?.message || 'An error occurred'
        : null;

    return { errorMessage };
}