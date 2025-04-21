// src/components/AddFolderForm.js
import React, { useState } from 'react';
import { backendUrl } from '../config';

function AddFolderForm({ onFolderAdded, setError }) {
    const [folderName, setFolderName] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!folderName.trim()) return;

        setIsSubmitting(true);
        setError('');

        try {
            const response = await fetch(`${backendUrl}/api/folders`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: folderName }),
            });

            const data = await response.json();

            if (!response.ok) {
                setError(data.error || 'Failed to create folder');
            } else {
                onFolderAdded();
                setFolderName('');
            }
        } catch (error) {
            console.error(error);
            setError('Failed to create folder');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="flex items-center">
            <input
                type="text"
                value={folderName}
                onChange={(e) => setFolderName(e.target.value)}
                placeholder="New Folder Name"
                className="p-2 border rounded-l focus:outline-none focus:ring focus:border-blue-300 transition-colors"
            />
            <button
                type="submit"
                disabled={!folderName.trim() || isSubmitting}
                className="px-4 py-2 bg-gray-600 text-white rounded-r hover:bg-gray-700 disabled:cursor-not-allowed transition-colors"
            >
                {isSubmitting ? 'Creating...' : 'Add Folder'}
            </button>
        </form>
    );
}

export default AddFolderForm;