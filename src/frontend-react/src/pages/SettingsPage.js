import React, { useState, useEffect } from 'react';
import { backendUrl } from '../config';

function SettingsPage() {
  const [spotifyClientId, setSpotifyClientId] = useState('');
  const [spotifyClientSecret, setSpotifyClientSecret] = useState('');
  const [soundcloudClientId, setSoundcloudClientId] = useState('');
  const [downloadPathPattern, setDownloadPathPattern] = useState('shared');
  const [downloadFolder, setDownloadFolder] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // Fetch settings when the component mounts.
  useEffect(() => {
    fetch(`${backendUrl}/api/settings`)
      .then(response => response.json())
      .then(data => {
        setSpotifyClientId(data.spotify_client_id);
        setSpotifyClientSecret(data.spotify_client_secret);
        setSoundcloudClientId(data.soundcloud_client_id);
        setDownloadPathPattern(data.download_path_pattern || 'shared');
        setDownloadFolder(data.download_folder || '');
      })
      .catch(() => setError('Error fetching settings'));
  }, []);

  // Save the updated settings.
  const handleSave = () => {
    if (!spotifyClientId || !spotifyClientSecret || !soundcloudClientId) {
      setError('Spotify Client ID, Spotify Client Secret, and SoundCloud Client ID are required.');
      return;
    }

    fetch(`${backendUrl}/api/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        spotify_client_id: spotifyClientId,
        spotify_client_secret: spotifyClientSecret,
        soundcloud_client_id: soundcloudClientId,
        download_path_pattern: downloadPathPattern
      })
    })
      .then(response => response.json())
      .then(data => {
        if (data.message) {
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
        helpText = 'Your Spotify Client ID can be found in your Spotify Developer Dashboard under your app settings. See Help for more info.';
      } else if (field === 'client_secret') {
        helpText = 'Your Spotify Client Secret is available in your Spotify Developer Dashboard. See Help for more info.';
      }
    } else if (platform === 'soundcloud') {
      helpText = 'SoundCloud Client ID required to sync with SoundCloud. See Help for more info.';
    }
    alert(helpText);
  };

  const handleLoginClick = () => {
    window.open(`${backendUrl}/api/spotify_auth/login`, '_blank');
  };

  // Check if the save button should be disabled
  const isSaveDisabled = !((spotifyClientId && spotifyClientSecret) || soundcloudClientId);

  // Get preview path for current pattern
  const getPreviewPath = (pattern) => {
    const basePath = downloadFolder || '/path/to/music_downloads';
    switch(pattern) {
      case 'artist':
        return `${basePath}/Artist Name/Track.mp3`;
      case 'playlist':
        return `${basePath}/Playlist Name/Track_123.mp3`;
      default:
        return `${basePath}/Track.mp3`;
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Settings</h1>
      {message && <div className="mb-4 p-3 bg-green-200 text-green-800 rounded">{message}</div>}
      {error && <div className="mb-4 p-3 bg-red-200 text-red-800 rounded">{error}</div>}
      <div className="py-5 border-y-2 ">
        {/* Spotify Settings */}
        <div className="mb-10">
          <h2 className="text-xl font-semibold mb-2">API Settings <span className="text-red-500">*</span></h2>
          <p className='py-2 mb-2'>These API keys are required to sync with Spotify or SoundCloud.</p>
          <div className="mb-4">
            <label className="block font-medium">Spotify Client ID <span className="text-red-500">*</span></label>
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
            <label className="block font-medium">Spotify Client Secret <span className="text-red-500">*</span></label>
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
          <div className="mb-4">
            <label className="block font-medium">SoundCloud Client ID <span className="text-red-500">*</span></label>
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
      </div>
      {/* Download Path Pattern Settings */}
      <div className="py-5 border-b-2">
        <h2 className="text-xl font-semibold mb-2">Download Organization</h2>
        <p className='py-2 mb-4'>Choose how downloaded tracks should be organized. This setting only affects new downloads.</p>
        
        <div className="space-y-3">
          <label className="flex items-start cursor-pointer">
            <input
              type="radio"
              name="downloadPathPattern"
              value="shared"
              checked={downloadPathPattern === 'shared'}
              onChange={(e) => setDownloadPathPattern(e.target.value)}
              className="mt-1 mr-3"
            />
            <div className="flex-1">
              <div className="font-medium">Shared Folder</div>
              <div className="text-sm text-gray-600">All tracks in one folder (current default)</div>
              <div className="text-xs text-gray-500 mt-1">Example: {getPreviewPath('shared')}</div>
            </div>
          </label>

          <label className="flex items-start cursor-pointer">
            <input
              type="radio"
              name="downloadPathPattern"
              value="artist"
              checked={downloadPathPattern === 'artist'}
              onChange={(e) => setDownloadPathPattern(e.target.value)}
              className="mt-1 mr-3"
            />
            <div className="flex-1">
              <div className="font-medium">Organize by Artist</div>
              <div className="text-sm text-gray-600">Each artist gets their own folder</div>
              <div className="text-xs text-gray-500 mt-1">Example: {getPreviewPath('artist')}</div>
            </div>
          </label>

          <label className="flex items-start cursor-pointer">
            <input
              type="radio"
              name="downloadPathPattern"
              value="playlist"
              checked={downloadPathPattern === 'playlist'}
              onChange={(e) => setDownloadPathPattern(e.target.value)}
              className="mt-1 mr-3"
            />
            <div className="flex-1">
              <div className="font-medium">Organize by Playlist</div>
              <div className="text-sm text-gray-600">Each playlist gets its own folder (tracks may be duplicated)</div>
              <div className="text-xs text-gray-500 mt-1">Example: {getPreviewPath('playlist')}</div>
            </div>
          </label>
        </div>

        {downloadFolder && (
          <div className="mt-4 p-3 bg-gray-100 rounded">
            <div className="text-sm font-medium text-gray-700">Download Location:</div>
            <div className="text-xs text-gray-600 mt-1 font-mono break-all">{downloadFolder}</div>
          </div>
        )}
      </div>
      {/* Spotify Login */}
      <div className="py-3 border-b-2 ">
        <div className="mb-4 ">
          <div className="mb-4"></div>
          <p className="mb-4"> <span className='font-medium'>Login with Spotify</span> to access your liked songs.</p>
          <button
            onClick={handleLoginClick}
            className="flex items-center px-3 py-2 rounded bg-green-500 text-white"
          >
            <img src="./icons/spotify.svg" alt="Spotify" className="w-6 h-6 mr-2 grayscale brightness-0 filter invert" />
            Login
          </button>
        </div>
      </div>
      <p className='py-2 mt-5'>Note, you may need to restart after making changes to settings.</p>
      <button
        onClick={handleSave}
        className={`mt-2 px-4 py-2 rounded ${isSaveDisabled ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 text-white'}`}
        disabled={isSaveDisabled}
      >
        Save Settings
      </button>
    </div>
  );
}

export default SettingsPage;