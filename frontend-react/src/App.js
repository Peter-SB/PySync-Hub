import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import Header from './components/Header';
import AddPlaylistForm from './components/AddPlaylistForm';
import PlaylistList from './components/PlaylistList';
import ExportStatus from './components/ExportStatus';

function App() {
  const [playlists, setPlaylists] = useState([]);
  const [exportStatus, setExportStatus] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Initialize socket.io to listen for real-time updates
  useEffect(() => {
    const socket = io(); // Connects to the same host
    socket.on('download_status', (data) => {
      // For simplicity, refresh the playlists on any download status update
      fetchPlaylists();
    });
    return () => socket.disconnect();
  }, []);

  // Fetch playlists from the API
  const fetchPlaylists = async () => {
    try {
      const response = await fetch('/api/playlists');
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
      const response = await fetch('/api/export');
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
    <div className="space-y-6">
      <Header onExport={handleExport} />
      <AddPlaylistForm onPlaylistAdded={fetchPlaylists} setError={setErrorMessage} />
      {errorMessage && (
        <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-400 rounded-lg">
          {errorMessage}
        </div>
      )}
      <PlaylistList playlists={playlists} refreshPlaylists={fetchPlaylists} />
      {exportStatus && <ExportStatus message={exportStatus} />}
    </div>
  );
}

export default App;
