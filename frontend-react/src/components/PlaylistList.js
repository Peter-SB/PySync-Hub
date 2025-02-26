import React, { useState } from 'react';
import PlaylistItem from './PlaylistItem';

function PlaylistList({ playlists, refreshPlaylists }) {
  const [selectedPlaylists, setSelectedPlaylists] = useState([]);

  // Called by PlaylistItem when a checkbox is toggled
  const handleCheckboxChange = (playlistId, isSelected) => {
    if (isSelected) {
      setSelectedPlaylists((prev) => [...prev, playlistId]);
    } else {
      setSelectedPlaylists((prev) => prev.filter((id) => id !== playlistId));
    }
  };

  // Handle sync action: if any playlist is selected, sync only those; otherwise sync all.
  const handleSync = async () => {
    const payload =
      selectedPlaylists.length > 0
        ? { playlist_ids: selectedPlaylists }
        : {};
    try {
      const response = await fetch('http://localhost:5000/api/playlists/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        console.error('Failed to sync playlists');
      }
      refreshPlaylists();
      // Optionally, clear selections after syncing
      setSelectedPlaylists([]);
    } catch (error) {
      console.error('Error syncing playlists', error);
    }
  };

  // Handle deletion of selected playlists
  const handleDelete = async () => {
    if (selectedPlaylists.length === 0) return;
    try {
      const response = await fetch('http://localhost:5000/api/playlists', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist_ids: selectedPlaylists }),
      });
      if (!response.ok) {
        console.error('Failed to delete playlists');
      }
      refreshPlaylists();
      setSelectedPlaylists([]);
    } catch (error) {
      console.error('Error deleting playlists', error);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button 
            onClick={handleSync}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            {selectedPlaylists.length > 0
              ? `Sync Selected (${selectedPlaylists.length})`
              : 'Sync All'}
          </button>
          {selectedPlaylists.length > 0 && (
            <button 
              onClick={handleDelete}
              className="flex items-center px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Delete Selected ({selectedPlaylists.length})
            </button>
          )}
        </div>
        {selectedPlaylists.length > 0 && (
          <div className="text-sm text-gray-700">
            {selectedPlaylists.length} selected
          </div>
        )}
      </div>
      <div id="playlist-list">
        {playlists.length ? (
          playlists.map((playlist) => (
            <PlaylistItem 
              key={playlist.id} 
              playlist={playlist} 
              refreshPlaylists={refreshPlaylists}
              isSelected={selectedPlaylists.includes(playlist.id)}
              onSelectChange={handleCheckboxChange}
            />
          ))
        ) : (
          <div className="p-4 text-center text-gray-500 bg-white rounded">
            No playlists added yet
          </div>
        )}
      </div>
    </div>
  );
}

export default PlaylistList;
