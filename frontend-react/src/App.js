import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import io from 'socket.io-client';
import AddPlaylistForm from './components/AddPlaylistForm';
import PlaylistList from './components/PlaylistList';
import ExportStatus from './components/ExportStatus';
import Sidebar from "./components/Sidebar";
import DownloadPage from './pages/DownloadPage';
import TrackPage from './pages/TrackPage';
import PlaylistPage from './pages/PlaylistPage';

function App() {
  const [playlists, setPlaylists] = useState([]);
  const [exportStatus, setExportStatus] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Initialize socket.io to listen for real-time updates
  useEffect(() => {
    const socket = io('http://localhost:5000'); // Connects to the same host
    socket.on('download_status', (data) => {
      console.log('Download status update:', data);
      // data is expected to be in the format: { id, status, progress }
      setPlaylists(prevPlaylists =>
        prevPlaylists.map(playlist =>
          playlist.id === data.id
            ? { 
                ...playlist, 
                download_status: data.status, 
                // Only update progress if it's provided in the event
                download_progress: data.progress !== undefined ? data.progress : playlist.download_progress,
                // Update downloaded_track_count based on progress
                downloaded_track_count: data.progress !== undefined ? Math.round((data.progress / 100) * playlist.track_count) : playlist.downloaded_track_count
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

  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <Sidebar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<DownloadPage playlists={playlists} setPlaylists={setPlaylists}/>} />
            <Route path="/playlist/:playlistId" element={<PlaylistPage />} />
            <Route path="/tracks" element={<TrackPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;