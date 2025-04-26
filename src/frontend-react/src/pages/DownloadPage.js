import React, { useState, useMemo } from 'react';
import AddPlaylistForm from '../components/AddPlaylistForm';
import PlaylistList from '../components/PlaylistList';
import PlaylistSortOrder from '../components/PlaylistSortOrder';
import ExportStatus from '../components/ExportStatus';
import { ErrorMessage } from '../components/ErrorMessage';
import { usePlaylists } from '../hooks/usePlaylists';
import { useSyncPlaylists, useDeletePlaylists, useExportAll } from '../hooks/usePlaylistMutations';

function DownloadPage() {
  const [exportMessage, setExportMessage] = useState('');
  const [selectedPlaylists, setSelectedPlaylists] = useState([]);
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("dec");
  const { data: playlists = [] } = usePlaylists();

  // React Query mutations
  const syncMutation = useSyncPlaylists();
  const deleteMutation = useDeletePlaylists();
  const exportMutation = useExportAll();

  // Sort playlists based on the selected sort criterion and order.
  // todo: move to PlaylistSortOrder?
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
      const result = await exportMutation.mutateAsync();
      setExportMessage("Export successful: " + result.export_path);
      // Clear export message after a few seconds
      setTimeout(() => setExportMessage(''), 3000);
    } catch (error) {
      console.error("Export error", error);
    }
  };

  // Handle sync action
  const handleSync = async () => {
    const playlistIds = selectedPlaylists.length > 0 ? selectedPlaylists : [];
    await syncMutation.mutateAsync(playlistIds);
    setSelectedPlaylists([]);
  };

  // Handle deletion of selected playlists
  const handleDelete = async () => {
    if (selectedPlaylists.length === 0) return;
    // Show confirmation dialog before deletion
    const confirmed = window.confirm(`Are you sure you want to delete ${selectedPlaylists.length} playlist(s)?`);
    if (!confirmed) return;
    // Proceed with deletion
    await deleteMutation.mutateAsync(selectedPlaylists);
    setSelectedPlaylists([]);

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
        <AddPlaylistForm />
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              className="flex items-center px-3 py-2 bg-gray-900 hover:bg-black text-white rounded-lg shadow-md"
              disabled={exportMutation.isLoading}
            >
              <span className="font-medium text-l">
                {exportMutation.isLoading ? 'Exporting...' : 'Export All'}
              </span>
              <div className="bg-white p-0.25 flex items-center justify-center rounded-lg ml-2">
                <img src="./icons/rekordbox.svg" alt="Rekordbox" className="h-6 w-6 rounded-lg m-0.5" />
                <img src="./icons/export.svg" alt="Export" className="h-6 w-6 rounded-lg" />
              </div>
            </button>
          </div>
          <div className="flex items-center gap-2 ml-auto">
            {/* <PlaylistSortOrder sortBy={sortBy} setSortBy={setSortBy} sortOrder={sortOrder} setSortOrder={setSortOrder} />  todo: reimplement*/}
            {selectedPlaylists.length > 0 && (
              <button
                onClick={handleDelete}
                className="flex items-center px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                disabled={deleteMutation.isLoading}
              >
                {deleteMutation.isLoading ? 'Deleting...' : `Delete Selected (${selectedPlaylists.length})`}
              </button>
            )}
            <button
              onClick={handleSync}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              disabled={syncMutation.isLoading}
            >
              {syncMutation.isLoading
                ? 'Syncing...'
                : (selectedPlaylists.length > 0
                  ? `Sync Selected (${selectedPlaylists.length})`
                  : 'Sync All')}
            </button>
          </div>
        </div>
      </div>

      <ErrorMessage />

      <PlaylistList
        selectedPlaylists={selectedPlaylists}
        onSelectChange={handleCheckboxChange}
      />

      {exportMessage && <ExportStatus message={exportMessage} />}
    </div>
  );
}

export default DownloadPage;
