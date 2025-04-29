import React from 'react';
import { useGlobalError } from '../contexts/GlobalErrorContext';
import { useQueryClient } from '@tanstack/react-query';

export function ErrorMessage() {
    const { error, setError } = useGlobalError();
    const queryClient = useQueryClient();

    // Set default options for queries and mutations to handle errors globally
    const onError = (error) => {
        setError(error);
    }
    queryClient.setDefaultOptions({
        queries: { onError },
        mutations: { onError },
    })

    if (!error) return null;

    const errorMessage = error instanceof Error ? error.message : String(error);

    return (
        <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-300 rounded relative">
            {errorMessage}
            <button
                onClick={() => setError(null)}
                className="absolute top-1 right-1 text-red-700 hover:text-red-900 focus:outline-none"
                aria-label="Close"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
            </button>
        </div>
    );
}