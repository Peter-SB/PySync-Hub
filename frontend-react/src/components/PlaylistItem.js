import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DownloadStatus from './DownloadStatus.js';
import { backendUrl } from '../config';

function PlaylistItem({ playlist, refreshPlaylists, isSelected, onSelectChange }) {
  const [isDisabled, setIsDisabled] = useState(playlist.disabled);
  const navigate = useNavigate();

  // Trigger a refresh (sync) for this playlist only
  const handleSyncClick = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/playlists/refresh`, {
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
      const response = await fetch(`${backendUrl}/api/download/${playlist.id}/cancel`, {
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

  // Toggle the disabled state of the playlist
  const handleToggleClick = async (playlistId, newState) => {
    // Optimistically update the UI
    setIsDisabled(newState);

    try {
      const response = await fetch(`${backendUrl}/api/playlists/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist_id: playlistId, disabled: newState }),
      });
      if (!response.ok) {
        throw new Error('Failed to toggle playlist state');
      }
      refreshPlaylists();
    } catch (error) {
      console.error('Error toggling playlist state', error);
      // Revert the UI update if there was an error
      setIsDisabled(!newState);
    }
  };

    // Navigate to the playlist tracks page
    const handlePlaylistClick = () => {
      navigate(`/playlist/${playlist.id}`);
    };

  return (
    <div className="flex flex-row items-center pt-1 pb-0">
      <div
        className={`flex items-center p-2 rounded border shadow transition-shadow my-1 px-4 flex-1 cursor-pointer ${isDisabled ? 'bg-gray-200 hover:shadow-none' : 'bg-white hover:shadow-md'
          }`}
          onClick={handlePlaylistClick}
      >
        <input
          type="checkbox"
          name="playlist_ids"
          value={playlist.id}
          className="mr-4 h-4 w-4"
          disabled={playlist.disabled}
          checked={isSelected}
          onClick={(e) => e.stopPropagation()}
          onChange={(e) => onSelectChange(playlist.id, e.target.checked)}
        />
        {playlist.image_url && (
          <img
            src={playlist.image_url}
            alt="Playlist cover"
            className="w-12 h-12 rounded-md object-cover mr-4 border border-gray-400"
          />
        )}
        <div className="flex-1">
          <h3 className="font-medium text-gray-900 flex items-center">
            <a 
              href={playlist.url} 
              target="_blank" 
              rel="noreferrer" 
              className="hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              {playlist.name}
            </a>
            {playlist.platform === "spotify" && (
            <img src="/icons/spotify.svg" alt="Spotify" className="w-5 h-5 ml-2" />
          )}
          {playlist.platform === "soundcloud" && (
            <img src="/icons/soundcloud.svg" alt="SoundCloud" className="w-4 h-4 p-0.5 ml-2" />
          )}
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
                Downloaded Tracks
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
      <label htmlFor={`toggle-${playlist.id}`} className="relative inline-flex items-center cursor-pointer ml-2 mr-10">
        <input
          type="checkbox"
          id={`toggle-${playlist.id}`}
          onChange={() => handleToggleClick(playlist.id, !isDisabled)}
          checked={isDisabled}
          className="sr-only peer"
        />
        <div className="relative w-[35px] h-[21px] bg-gray-400 border border-gray-300 rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:ring-gray-600 disabled:opacity-50 disabled:pointer-events-none
                peer-checked:bg-gray-100
                before:inline-block before:w-4 before:h-4 before:bg-white before:rounded-full before:shadow before:transition-all before:ease-in-out before:duration-200
                before:translate-x-[14px] peer-checked:before:translate-x-0">
        </div>
      </label>
    </div>
  );
}

export default PlaylistItem;