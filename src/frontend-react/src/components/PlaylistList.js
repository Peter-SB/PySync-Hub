// src/components/PlaylistList.js
import React from 'react';
import PlaylistItem from './PlaylistItem';
import './CustomScrollbar.css';
import { Link } from 'react-router-dom';

function PlaylistList({ playlists, fetchPlaylists, selectedPlaylists, onSelectChange }) {
  return (
    <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
      <div id="playlist-list">
        {playlists.length ? (
          playlists.map((playlist) => (
            <PlaylistItem
              key={playlist.id}
              playlist={playlist}
              fetchPlaylists={fetchPlaylists}
              isSelected={selectedPlaylists.includes(playlist.id)}
              onSelectChange={onSelectChange}
            />
          ))
        ) : (
          <div className="p-4 text-center text-gray-500 bg-white rounded">
            No playlists added yet. If this is your first time using the app, make sure to read the Help page and set your <Link to="/settings" className="text-blue-500 hover:underline">Settings</Link>.
          </div>
        )}
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-2 bg-gradient-to-t from-gray-100 to-transparent pointer-events-none"></div>
    </div>
  );
}

export default PlaylistList;
