// src/pages/PlaylistTracksPage.js
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { backendUrl } from '../config';

function PlaylistPage() {
    const { playlistId } = useParams();
    const [tracks, setTracks] = useState([]);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchPlaylistTracks = async () => {
            try {
                const response = await fetch(`${backendUrl}/api/playlist/${playlistId}/tracks`);
                const data = await response.json();
                if (response.ok) {
                    setTracks(data);
                } else {
                    setError(data.error || 'Failed to fetch playlist tracks');
                }
            } catch (err) {
                console.error(err);
                setError('Error fetching playlist tracks');
            }
        };

        fetchPlaylistTracks();
    }, [playlistId]);

    return (
        <div className="flex flex-col h-screen p-5">
            <h1 className="text-3xl font-bold mb-4">Playlist Tracks</h1>
            {error && (
                <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-400 rounded">
                    {error}
                </div>
            )}
            <div className="flex-1 bg-white shadow rounded-lg p-4 flex-1 min-h-0 overflow-y-auto p-2 custom-scrollbar">
                <div id="track-table" className="">
                    {tracks.length > 0 ? (
                        <ul className="space-y-2">
                            {tracks.map((track, index) => (
                                <li key={track.platform_id} className="flex px-4 py-1 bg-white border rounded shadow hover:shadow-md flex items-center">
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
                                    <div className="flex flex-row text-sm flex-grow">
                                        <h2 className="font-semibold mr-2 hover:underline">
                                            <a href={track.download_url} target="_blank" rel="noopener noreferrer">
                                                {track.name}
                                            </a>
                                        </h2>
                                        <p className="text-gray-600 mr-2">{track.artist}</p>
                                        {track.album && <p className="text-gray-500">{track.album}</p>}
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
                                            <p className="text-green-700 text-sm mt-1">
                                                Location: {track.download_location}
                                            </p>
                                        )}
                                    </div>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <div>No tracks found for this playlist.</div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default PlaylistPage;
