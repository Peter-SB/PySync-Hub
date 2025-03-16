import React, { useState, useEffect } from 'react';
import { backendUrl } from '../config';

function TrackPage() {
  const [tracks, setTracks] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchTracks();
  }, []);

  const fetchTracks = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/tracks`);
      const data = await response.json();
      if (response.ok) {
        setTracks(data);
      } else {
        setError(data.error || 'Failed to fetch tracks');
      }
    } catch (err) {
      console.error(err);
      setError('Error fetching tracks');
    }
  };

  // Filter tracks based on search input
  const filteredTracks = tracks.filter(track =>
    track.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    track.artist.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (track.album && track.album.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div id="track-page" className="flex flex-col h-screen p-4 pt-2">
      {/* Search Bar Header */}
      <div id="header-box" className="bg-white p-5 pb-4 pt-7 rounded-lg mb-2 shadow flex flex-col">
        <div className="flex items-center flex-grow mb-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Search by title, artist, or album..."
            className="w-full p-3 text-gray-800 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="text-gray-600 text-sm text-left ml-9">
          {filteredTracks.length} {filteredTracks.length === 1 ? 'song' : 'songs'} found
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-400 rounded">
          {error}
        </div>
      )}

      {/* Track List */}
      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
        <div id="track-table">
          {filteredTracks.length > 0 ? (
            <ul className="">
              {filteredTracks.map((track, index) => (
                <li
                  key={track.platform_id}
                  className="flex px-4 py-1 bg-grey-100 border-y flex items-center"
                >
                  <div className="text-l mr-3 w-7">{index + 1}.</div>
                  <div className="w-9 h-9 mr-4">
                    {track.album_art_url && (
                      <img
                        src={track.album_art_url}
                        alt={track.name}
                        className="w-9 h-9 rounded-md object-cover border border-gray-300"
                      />
                    )}
                  </div>
                  <div className="flex flex-row text-sm flex-grow items-center">
                    <h2 className="font-semibold mr-2 hover:underline flex items-center">
                      <a href={track.download_url} target="_blank" rel="noopener noreferrer">
                        {track.name}
                      </a>
                    </h2>
                    <p className="text-gray-600 mr-2">{track.artist}</p>
                    {track.album && <p className="text-gray-500">{track.album}</p>}
                    {track.platform === "spotify" && (
                        <img
                          src="/icons/spotify.svg"
                          alt="Spotify"
                          className="w-5 h-5 ml-2 inline"
                        />
                      )}
                      {track.platform === "soundcloud" && (
                        <img
                          src="/icons/soundcloud.svg"
                          alt="SoundCloud"
                          className="w-3 h-3 ml-2 inline"
                        />
                      )}
                  </div>
                  <div className="flex flex-row items-end justify-end">
                    {track.notes_errors && track.notes_errors !== "Already Downloaded, Skipped" && track.notes_errors !== "Successfully Downloaded" && (
                      <div className="flex items-center ml-4">
                        <div className="flex items-center justify-center bg-red-500 text-white rounded-full w-8 h-8 mr-2">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M12 2a10 10 0 110 20 10 10 0 010-20z" />
                          </svg>
                        </div>
                        <div className="text-red-700 text-sm">{track.notes_errors}</div>
                      </div>
                    )}
                    {track.download_location && (
                      <p className="text-green-700 text-xs mt-1">
                        Location: {track.download_location}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-gray-500 text-center mt-5">No tracks found.</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TrackPage;
