import React, { useState, useEffect } from 'react';

function SettingsPage() {
  const [spotifyClientId, setSpotifyClientId] = useState('');
  const [spotifyClientSecret, setSpotifyClientSecret] = useState('');
  const [soundcloudClientId, setSoundcloudClientId] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // Fetch settings when the component mounts.
  useEffect(() => {
    fetch('http://localhost:5000/api/settings')
      .then(response => response.json())
      .then(data => {
        setSpotifyClientId(data.spotify_client_id);
        setSpotifyClientSecret(data.spotify_client_secret);
        setSoundcloudClientId(data.soundcloud_client_id);
      })
      .catch(() => setError('Error fetching settings'));
  }, []);

  // Save the updated settings.
  const handleSave = () => {
    if (!spotifyClientId || !spotifyClientSecret || !soundcloudClientId) {
      setError('Spotify Client ID, Spotify Client Secret, and SoundCloud Client ID are required.');
      return;
    }

    fetch('http://localhost:5000/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        spotify_client_id: spotifyClientId,
        spotify_client_secret: spotifyClientSecret,
        soundcloud_client_id: soundcloudClientId
      })
    })
      .then(response => response.json())
      .then(data => {
         if(data.message) {
             setMessage(data.message);
             setError('');
         } else {
             setError(data.error || 'Error updating settings');
         }
      })
      .catch(() => setError('Error updating settings'));
  };

  // Display help text for the respective fields.
  const showHelp = (platform, field) => {
    let helpText = '';
    if (platform === 'spotify') {
      if (field === 'client_id') {
         helpText = 'Your Spotify Client ID can be found in your Spotify Developer Dashboard under your app settings.';
      } else if (field === 'client_secret') {
         helpText = 'Your Spotify Client Secret is available in your Spotify Developer Dashboard. Keep it confidential!';
      }
    } else if (platform === 'soundcloud') {
      helpText = 'Your SoundCloud Client ID is provided when you register your application with SoundCloud.';
    }
    alert(helpText);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Settings</h1>
      {message && <div className="mb-4 p-3 bg-green-200 text-green-800 rounded">{message}</div>}
      {error && <div className="mb-4 p-3 bg-red-200 text-red-800 rounded">{error}</div>}

      {/* Spotify Settings */}
      <div className="mb-10">
        <h2 className="text-xl font-semibold mb-2">Spotify Settings</h2>
        <div className="mb-4">
          <label className="block font-medium">Spotify Client ID</label>
          <div className="flex items-center">
            <input 
              type="text" 
              value={spotifyClientId}
              onChange={(e) => setSpotifyClientId(e.target.value)}
              className="flex-1 p-2 border rounded"
            />
            <button 
              onClick={() => showHelp('spotify', 'client_id')}
              className="ml-2 px-3 py-1 bg-gray-300 rounded"
            >
              ?
            </button>
          </div>
        </div>
        <div className="mb-4">
          <label className="block font-medium">Spotify Client Secret</label>
          <div className="flex items-center">
            <input 
              type="text" 
              value={spotifyClientSecret}
              onChange={(e) => setSpotifyClientSecret(e.target.value)}
              className="flex-1 p-2 border rounded"
            />
            <button 
              onClick={() => showHelp('spotify', 'client_secret')}
              className="ml-2 px-3 py-1 bg-gray-300 rounded"
            >
              ?
            </button>
          </div>
        </div>
      </div>

      {/* SoundCloud Settings */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-2">SoundCloud Settings</h2>
        <div className="mb-4">
          <label className="block font-medium">SoundCloud Client ID</label>
          <div className="flex items-center">
            <input 
              type="text" 
              value={soundcloudClientId}
              onChange={(e) => setSoundcloudClientId(e.target.value)}
              className="flex-1 p-2 border rounded"
            />
            <button 
              onClick={() => showHelp('soundcloud')}
              className="ml-2 px-3 py-1 bg-gray-300 rounded"
            >
              ?
            </button>
          </div>
        </div>
      </div>

      <button onClick={handleSave} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded">
        Save Settings
      </button>
    </div>
  );
}

export default SettingsPage;