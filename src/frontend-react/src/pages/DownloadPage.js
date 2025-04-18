import React, { useState, useMemo } from 'react';
import AddPlaylistForm from '../components/AddPlaylistForm';
import PlaylistList from '../components/PlaylistList';
import PlaylistSortOrder from '../components/PlaylistSortOrder';
import { backendUrl } from '../config';

function DownloadPage({ playlists, fetchPlaylists, errorMessage, setErrorMessage }) {
  const [exportStatus, setExportStatus] = useState('');
  const [selectedPlaylists, setSelectedPlaylists] = useState([]);
  const [sortBy, setSortBy] = useState("created_at"); // default sort by name
  const [sortOrder, setSortOrder] = useState("dec"); // ascending order by default

  // Sort playlists based on the selected sort criterion and order.
  const sortedPlaylists = useMemo(() => {
    return playlists.slice().sort((a, b) => {
      let aVal = a[sortBy];
      let bVal = b[sortBy];

      if (sortBy === "name") {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      } else {
        // For date fields, convert to Date objects (using a fallback for null values)
        aVal = aVal ? new Date(aVal) : new Date(0);
        bVal = bVal ? new Date(bVal) : new Date(0);
      }

      if (sortOrder === "asc") {
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      } else {
        return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
      }
    });
  }, [playlists, sortBy, sortOrder]);

  // Handle export action
  const handleExport = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/export`);
      const data = await response.json();
      if (response.ok) {
        setExportStatus("Export successful: " + data.export_path);
        // Clear export status after a few seconds
        setTimeout(() => setExportStatus(''), 3000);
      } else {
        setErrorMessage(data.error);
      }
    } catch (error) {
      console.error("Export error", error);
      setErrorMessage("Export failed");
    }
  };

  // Handle sync action
  const handleSync = async () => {
    const payload = selectedPlaylists.length > 0 ? { playlist_ids: selectedPlaylists } : {};
    try {
      const response = await fetch(`${backendUrl}/api/playlists/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        console.error('Failed to sync playlists');
      }
      fetchPlaylists();
      setSelectedPlaylists([]);
    } catch (error) {
      console.error('Error syncing playlists', error);
    }
  };

  // Handle deletion of selected playlists
  const handleDelete = async () => {
    if (selectedPlaylists.length === 0) return;
    try {
      const response = await fetch(`${backendUrl}/api/playlists`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist_ids: selectedPlaylists }),
      });
      if (!response.ok) {
        console.error('Failed to delete playlists');
      }
      fetchPlaylists();
      setSelectedPlaylists([]);
    } catch (error) {
      console.error('Error deleting playlists', error);
    }
  };

  // Callback for checkbox selection in PlaylistList
  const handleCheckboxChange = (playlistId, isSelected) => {
    if (isSelected) {
      setSelectedPlaylists(prev => [...prev, playlistId]);
    } else {
      setSelectedPlaylists(prev => prev.filter(id => id !== playlistId));
    }
  };

  return (
    <div id="download-page" className="flex flex-col h-screen p-4 pt-2">
      {/* Header box */}
      <div id="header-box" className="bg-white p-4 rounded-lg mb-1 shadow">
        <h1 className="text-3xl font-semibold text-gray-800 mb-7">Playlist Downloads</h1>
        <AddPlaylistForm onPlaylistAdded={fetchPlaylists} setError={setErrorMessage} />
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              className="flex items-center px-3 py-2 bg-gray-900 hover:bg-black text-white rounded-lg shadow-md"
            >
              <span className="font-medium text-l">Export All</span>
              <div className="bg-white p-0.25 flex items-center justify-center rounded-lg ml-2">
                <img src="./icons/rekordbox.svg" alt="Rekordbox" className="h-6 w-6 rounded-lg m-0.5" />
                <img src="./icons/export.svg" alt="Export" className="h-6 w-6 rounded-lg" />
              </div>
            </button>
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <PlaylistSortOrder sortBy={sortBy} setSortBy={setSortBy} sortOrder={sortOrder} setSortOrder={setSortOrder} />
            {selectedPlaylists.length > 0 && (
              <button
                onClick={handleDelete}
                className="flex items-center px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Delete Selected ({selectedPlaylists.length})
              </button>
            )}
            <button
              onClick={handleSync}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              {selectedPlaylists.length > 0
                ? `Sync Selected (${selectedPlaylists.length})`
                : 'Sync All'}
            </button>
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-300 rounded">
          {errorMessage}
        </div>
      )}

      <PlaylistList
        playlists={sortedPlaylists}
        fetchPlaylists={fetchPlaylists}
        selectedPlaylists={selectedPlaylists}
        onSelectChange={handleCheckboxChange}
      />

      {exportStatus && (
        <div className="fixed bottom-5 left-1/2 transform -translate-x-1/2 z-50 bg-green-500 text-white text-center py-3 px-6 rounded max-w-4xl w-full md:w-3/4 lg:w-1/2 shadow-lg">
          {exportStatus}
        </div>
      )}
    </div>
  );
}

export default DownloadPage;
