import React, { useState, useEffect } from 'react';
import { backendUrl } from '../config';

function TrackPage() {
  const [tracks, setTracks] = useState([]);
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

return (
    <div className="p-5">
        <h1 className="text-3xl font-bold mb-4">All Tracks</h1>
        {error && (
            <div className="p-4 mb-3 text-sm text-red-700 bg-red-100 border border-red-400 rounded">
                {error}
            </div>
        )}
        {tracks.length > 0 ? (
            <ul className="space-y-2 overflow-y-auto max-h-[calc(100vh-100px)] p-3 bg-white" style={{ backgroundColor: 'rgb(249, 249, 249)' }}>
                {tracks.map((track, index) => (
                    <li key={track.platform_id} className="p-1 bg-white rounded shadow hover:shadow-md flex items-center">
                        <span className="mx-4 text-sm">{index + 1}</span>
                        {track.album_art_url && (
                            <img
                                src={track.album_art_url}
                                alt={track.name}
                                className="w-8 h-8 rounded-md object-cover mr-4"
                            />
                        )}
                        <div className="flex flex-row text-sm">
                            <h2 className="font-semibold mr-2">{track.name}</h2>
                            <p className="text-gray-600 mr-2">{track.artist}</p>
                            {track.album && <p className="text-gray-500">{track.album}</p>}
                        </div>
                    </li>
                ))}
            </ul>
        ) : (
            <div>No tracks found.</div>
        )}
    </div>
);
}

export default TrackPage;
