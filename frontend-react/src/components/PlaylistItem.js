import React from 'react';
import DownloadStatus from './DownloadStatus.js';


function PlaylistItem({ playlist, refreshPlaylists, isSelected, onSelectChange }) {
  // Trigger a refresh (sync) for this playlist only
  const handleSyncClick = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/playlists/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist_ids: [playlist.id] }),
      });
      if (!response.ok) {
        console.error('Failed to sync playlist');
      }
    } catch (error) {
      console.error('Error syncing playlist', error);
    }
  };

  // Cancel an ongoing download for this playlist
  const handleCancelClick = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/download/${playlist.id}/cancel`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        console.error('Failed to cancel download');
      }
      refreshPlaylists();
    } catch (error) {
      console.error('Error cancelling download', error);
    }
  };

  return (
    <div
      className={`flex items-center p-2 rounded shadow-sm transition-shadow my-2 mx-1 ${playlist.disabled ? 'bg-gray-200 hover:shadow-none' : 'bg-white hover:shadow-md'
        }`}
    >
      <input
        type="checkbox"
        name="playlist_ids"
        value={playlist.id}
        className="mr-4 h-4 w-4"
        disabled={playlist.disabled}
        checked={isSelected}
        onChange={(e) => onSelectChange(playlist.id, e.target.checked)}
      />
      {playlist.image_url && (
        <img
          src={playlist.image_url}
          alt="Playlist cover"
          className="w-14 h-14 rounded-md object-cover mr-4"
        />
      )}
      <div className="flex-1">
        <h3 className="font-medium text-gray-900">
          <a href={playlist.url} target="_blank" rel="noreferrer" className="hover:underline">
            {playlist.name}
          </a>
        </h3>
        <div className="text-sm text-gray-600">
          {playlist.last_synced
            ? `Last synced: ${new Date(playlist.last_synced).toLocaleString()}`
            : 'Not synced'}
        </div>
      </div>
      <div className={`relative ml-auto p-2 text-sm ${playlist.disabled ? 'text-gray-500' : 'text-gray-600'} group`}>
        {playlist.downloaded_track_count === playlist.track_count ? (
          <>
            <span>{playlist.track_count}</span>
            <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition duration-150 pointer-events-none whitespace-nowrap">
              Total Tracks
            </span>
          </>
        ) : (
          <>
            <span>{playlist.downloaded_track_count} / {playlist.track_count}</span>
            <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition duration-150 pointer-events-none whitespace-nowrap">
              Downloaded / Total Tracks
            </span>
          </>
        )}
      </div>
      <DownloadStatus playlist={playlist} handleSyncClick={handleSyncClick} handleCancelClick={handleCancelClick} />
    </div>
  );
}

export default PlaylistItem;
