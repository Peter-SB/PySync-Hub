import React from 'react';
import { useQueryErrors } from '../hooks/useQueryErrors';

export function QueryErrorMessage() {
    const { errorMessage } = useQueryErrors();

    if (!errorMessage) return null;

    return (
        <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-300 rounded">
            {errorMessage}
        </div>
    );
}