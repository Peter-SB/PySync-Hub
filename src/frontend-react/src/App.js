import React from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';  // Use this for production and when running in Electron. Because Electron uses file:// protocol and BrowserRouter doesn't work with file:// protocol
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useSocketPlaylistUpdates } from './hooks/useSocketPlaylistUpdates';

import Sidebar from "./components/Sidebar";
import DownloadPage from './pages/DownloadPage';
import TrackPage from './pages/TrackPage';
import PlaylistPage from './pages/PlaylistPage';
import SettingsPage from './pages/SettingsPage';
import TracklistsPage from './pages/TracklistsPage';
import TracklistDetailPage from './pages/TracklistDetailPage';
import { GlobalErrorProvider } from './contexts/GlobalErrorContext';


const qc = new QueryClient({
  defaultOptions: {
    queries: {
      onError: (error) => {
        console.error('Global query error:', error);
      },
      retry: 1,
    },
    mutations: {
      onError: (error) => {
        console.error('Global mutation error:', error);
      },
      retry: 1,
    },
  },
});



// Main application component wrapped in React Query Client Provider.
function AppContent() {
  useSocketPlaylistUpdates();

  return (
    <Router>
      <div className="flex min-h-screen bg-gray-100">
        <Sidebar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<DownloadPage />} />
            <Route path="/playlist/:playlistId" element={<PlaylistPage />} />
            <Route path="/tracks" element={<TrackPage />} />
            <Route path="/tracklists" element={<TracklistsPage />} />
            <Route path="/tracklist/:tracklistId" element={<TracklistDetailPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function App() {
  return (
    <GlobalErrorProvider>
      <QueryClientProvider client={qc}>
        <AppContent />
      </QueryClientProvider>
    </GlobalErrorProvider>

  );
}

export default App;
