import React from 'react';
import PlaylistItem from './PlaylistItem';

function PlaylistList({ playlists, refreshPlaylists }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        {/* You can add additional controls for sync/delete here */}
        <button 
          onClick={refreshPlaylists}
          className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          Sync All
        </button>
      </div>
      <div id="playlist-list">
        {playlists.length ? (
          playlists.map((playlist) => (
            <PlaylistItem key={playlist.id} playlist={playlist} refreshPlaylists={refreshPlaylists} />
          ))
        ) : (
          <div className="p-4 text-center text-gray-500 bg-white rounded-lg">
            No playlists added yet
          </div>
        )}
      </div>
    </div>
  );
}

export default PlaylistList;
