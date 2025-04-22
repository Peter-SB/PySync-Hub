import React, { useState, useEffect, useCallback } from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';  // Use this for production and when running in Electron. Because Electron uses file:// protocol and BrowserRouter doesn't work with file:// protocol

import io from 'socket.io-client';
import Sidebar from "./components/Sidebar";
import DownloadPage from './pages/DownloadPage';
import TrackPage from './pages/TrackPage';
import PlaylistPage from './pages/PlaylistPage';
import SettingsPage from './pages/SettingsPage';

import { backendUrl } from './config';


function App() {
  const [playlists, setPlaylists] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');

  // Initialize socket.io to listen for real-time updates
  useEffect(() => {
    const socket = io(backendUrl);
    socket.on('download_status', (data) => {
      console.log('Download status update:', data);

      setPlaylists(prevPlaylists =>
        prevPlaylists.map(playlist =>
          playlist.id === data.id
            ? {
              ...playlist,
              download_status: data.status,
              download_progress: data.progress !== undefined ? data.progress : playlist.download_progress,
              downloaded_track_count: data.progress !== undefined ? Math.round((data.progress / 100) * playlist.tracks.length) : playlist.downloaded_track_count
            }
            : playlist
        )
      );
    });
    return () => socket.disconnect();
  }, []);

  const fetchPlaylists = useCallback(async () => {
    try {
      const response = await fetch(`${backendUrl}/api/playlists`);
      const data = await response.json();
      setPlaylists(data);
    } catch (error) {
      console.error("Server Error", error);
      setErrorMessage("Server Error: " + error.message + ". Please check if the server is running. See Help");
    }
  }, []);

  // folderReactor-todo: Getting Folder logging here?

  useEffect(() => {
    fetchPlaylists();
  }, [fetchPlaylists]);

  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <Sidebar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<DownloadPage playlists={playlists} fetchPlaylists={fetchPlaylists} errorMessage={errorMessage} setErrorMessage={setErrorMessage} />} />
            <Route path="/playlist/:playlistId" element={<PlaylistPage playlists={playlists} />} />
            <Route path="/tracks" element={<TrackPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;