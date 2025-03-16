// src/pages/PlaylistPage.js
import React, { useState, useEffect } from 'react';
import AddPlaylistForm from '../components/AddPlaylistForm';
import PlaylistList from '../components/PlaylistList';
import { backendUrl } from '../config';


function DownloadPage({playlists, setPlaylists}) {
  const [errorMessage, setErrorMessage] = useState('');
  const [exportStatus, setExportStatus] = useState('');

  // Fetch playlists from the API
  const fetchPlaylists = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/playlists`);
      const data = await response.json();
      setPlaylists(data);
    } catch (error) {
      console.error("Error fetching playlists", error);
      setErrorMessage("Error fetching playlists");
    }
  };

  useEffect(() => {
    fetchPlaylists();
  }, []);

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

  return (
    <div className="flex flex-col h-screen p-5">
      <h1 className="text-3xl font-bold p-6 py-3">Playlist Downloads</h1>
      <AddPlaylistForm onPlaylistAdded={fetchPlaylists} setError={setErrorMessage} />
      {errorMessage && (
        <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-300 rounded">
          {errorMessage}
        </div>
      )}
      <PlaylistList 
        playlists={playlists} 
        refreshPlaylists={fetchPlaylists} 
        onExport={handleExport} 
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