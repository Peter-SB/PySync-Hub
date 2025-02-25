import React from 'react';

function PlaylistItem({ playlist, refreshPlaylists }) {
  // This component will eventually render the playlist details,
  // download progress, sync button, toggle switch, etc.
  return (
    <div className={`flex items-center p-4 rounded-lg shadow-sm transition-shadow ${playlist.disabled ? 'bg-gray-200 hover:shadow-none' : 'bg-white hover:shadow-md'}`}>
      <input 
        type="checkbox" 
        name="playlist_ids" 
        value={playlist.id} 
        className="mr-4 h-4 w-4" 
        disabled={playlist.disabled} 
      />
      {playlist.image_url && (
        <img src={playlist.image_url} alt="Playlist cover" className="w-14 h-14 rounded-lg object-cover mr-4" />
      )}
      <div className="flex-1">
        <h3 className="font-medium text-gray-900">
          <a href={playlist.url} target="_blank" rel="noreferrer" className="hover:underline">
            {playlist.name}
          </a>
        </h3>
        <div className="text-sm text-gray-600">
          {playlist.last_synced ? `Last synced: ${new Date(playlist.last_synced).toLocaleString()}` : 'Not synced'}
        </div>
      </div>
      {/* Placeholder for download progress and sync actions */}
      <div id={`download-status-${playlist.id}`}>
        {/* These controls will be added in further iterations */}
      </div>
    </div>
  );
}

export default PlaylistItem;
