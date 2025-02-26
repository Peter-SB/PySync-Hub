import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import AddPlaylistForm from './components/AddPlaylistForm';
import PlaylistList from './components/PlaylistList';
import ExportStatus from './components/ExportStatus';
import Sidebar from "./components/Sidebar";

function App() {
  const [playlists, setPlaylists] = useState([]);
  const [exportStatus, setExportStatus] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Initialize socket.io to listen for real-time updates
  useEffect(() => {
    const socket = io('http://localhost:5000'); // Connects to the same host
    socket.on('download_status', (data) => {
      // data is expected to be in the format: { id, status, progress }
      setPlaylists(prevPlaylists =>
        prevPlaylists.map(playlist =>
          playlist.id === data.id
            ? { 
                ...playlist, 
                download_status: data.status, 
                // Only update progress if it's provided in the event
                download_progress: data.progress !== undefined ? data.progress : playlist.download_progress 
              }
            : playlist
        )
      );
    }); 
    return () => socket.disconnect();
  }, []);

  // Fetch playlists from the API
  const fetchPlaylists = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/playlists');
      console.log(response);
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
      const response = await fetch('http://localhost:5000/api/export');
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
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <main className="flex-1 p-6">
        <div className="space-y-6">
          <AddPlaylistForm onPlaylistAdded={fetchPlaylists} setError={setErrorMessage} />
          {errorMessage && (
            <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-400 rounded">
              {errorMessage}
            </div>
          )}
          <PlaylistList playlists={playlists} refreshPlaylists={fetchPlaylists} onExport={handleExport} />
          {exportStatus && <ExportStatus message={exportStatus} />}
        </div>
      </main>
      <div className="w-24"></div> {/* Blank space on the right */}
    </div>
  );
}

export default App;
