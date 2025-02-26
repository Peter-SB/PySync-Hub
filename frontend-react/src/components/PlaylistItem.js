import React from 'react';
import DownloadStatus from './DownloadStatus';

function PlaylistItem({ playlist, refreshPlaylists, isSelected, onSelectChange }) {
  return (
    <div className={`flex items-center p-2 rounded shadow-sm transition-shadow my-2 mx-1 ${playlist.disabled ? 'bg-gray-200 hover:shadow-none' : 'bg-white hover:shadow-md'}`}>
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
        <img src={playlist.image_url} alt="Playlist cover" className="w-14 h-14 rounded-md object-cover mr-4" />
      )}
      <div className="flex-1">
        <h3 className="font-medium text-gray-900 flex items-center">
          <a href={playlist.url} target="_blank" rel="noreferrer" className="hover:underline">
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
          {playlist.last_synced ? `Last synced: ${new Date(playlist.last_synced).toLocaleString()}` : 'Not synced'}
        </div>
      </div>
      <DownloadStatus playlist={playlist} refreshPlaylists={refreshPlaylists} />
    </div>
  );
}

export default PlaylistItem;
