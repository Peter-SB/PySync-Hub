import React, { useState } from 'react';
import { backendUrl } from '../config';

function FolderActions({ fetchPlaylists, setErrorMessage }) {
  const [showFolderForm, setShowFolderForm] = useState(false);
  const [folderName, setFolderName] = useState('');
  const [loading, setLoading] = useState(false);

  const handleCreateFolder = async (e) => {
    e.preventDefault();
    if (!folderName.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/folders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: folderName, parent_id: null }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to create folder');
      }

      setFolderName('');
      setShowFolderForm(false);
      fetchPlaylists(); // Refresh playlists to show the new folder
    } catch (error) {
      console.error('Error creating folder:', error);
      setErrorMessage(error.message || 'Error creating folder');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mb-4">
      {!showFolderForm ? (
        <button
          onClick={() => setShowFolderForm(true)}
          className="flex items-center px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg shadow-sm"
        >
          <span className="mr-2">📁</span>
          <span className="font-medium">New Folder</span>
        </button>
      ) : (
        <form onSubmit={handleCreateFolder} className="flex items-center gap-2">
          <input
            type="text"
            value={folderName}
            onChange={(e) => setFolderName(e.target.value)}
            placeholder="Folder name"
            className="flex-grow px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            autoFocus
          />
          <button
            type="submit"
            disabled={loading || !folderName.trim()}
            className={`px-4 py-2 rounded-lg ${
              loading || !folderName.trim() 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
            } text-white`}
          >
            {loading ? 'Creating...' : 'Create'}
          </button>
          <button
            type="button"
            onClick={() => setShowFolderForm(false)}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg"
          >
            Cancel
          </button>
        </form>
      )}
    </div>
  );
}

export default FolderActions;