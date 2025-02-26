import React from 'react';

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
        <h3 className="font-medium text-gray-900">
          <a href={playlist.url} target="_blank" rel="noreferrer" className="hover:underline">
            {playlist.name}
          </a>
        </h3>
        <div className="text-sm text-gray-600">
          {playlist.last_synced ? `Last synced: ${new Date(playlist.last_synced).toLocaleString()}` : 'Not synced'}
        </div>
      </div>
      <div id={`download-status-${playlist.id}`}>
        {/* Additional controls (e.g., download progress) can be added here */}
      </div>
    </div>
  );
}

export default PlaylistItem;
