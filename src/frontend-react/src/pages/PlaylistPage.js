// src/pages/PlaylistTracksPage.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { backendUrl } from '../config';
import TrackModal from '../components/TrackModal';

function PlaylistPage({ playlists }) {
    const { playlistId } = useParams();
    const [tracks, setTracks] = useState([]);
    const [error, setError] = useState('');
    const [selectedTrack, setSelectedTrack] = useState(null);
    const navigate = useNavigate();

    const playlistInfo = playlists.find(pl => String(pl.id) === playlistId);

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

    // Delete the playlist and navigate away
    const handleDeleteClick = async () => {
        if (!window.confirm('Are you sure you want to delete this playlist?')) return;
        try {
            const response = await fetch(`${backendUrl}/api/playlists/${playlistInfo.id}`, {
                method: 'DELETE',
            });
            if (response.ok) {
                navigate('/');
            } else {
                console.error('Failed to delete playlist');
            }
        } catch (error) {
            console.error('Error deleting playlist', error);
        }
    };

    // Update track in state after a successful edit
    const handleUpdateTrack = (updatedTrack) => {
        setTracks(tracks.map(t => (t.id === updatedTrack.id ? updatedTrack : t)));
    };

    return (
        <div id="playlist-page" className="flex flex-col h-screen p-4 pt-2">
            {/* Playlist Info Header box */}
            <div id="header-box" className="bg-white p-5 rounded-lg mb-1 shadow flex items-center">
                {playlistInfo ? (
                    <div className="flex flex-col sm:flex-row justify-between items-center justify-end w-full">
                        {/* Left section: image and info */}
                        <div className="flex items-center">
                            {playlistInfo.image_url && (
                                <img
                                    src={playlistInfo.image_url}
                                    alt="Playlist cover"
                                    className="w-24 h-24 rounded-md object-cover mr-4 border border-gray-400"
                                />
                            )}
                            <div className="flex flex-col">
                                <h1 className="text-3xl font-semibold text-gray-800 mb-1">
                                    <a href={playlistInfo.url} target="_blank" rel="noreferrer" className="hover:underline">
                                        {playlistInfo.name}
                                    </a>
                                    {playlistInfo.platform === "spotify" && (
                                        <img
                                            src="./icons/spotify.svg"
                                            alt="Spotify"
                                            className="w-8 h-8 ml-3 mb-1 inline"
                                        />
                                    )}
                                    {playlistInfo.platform === "soundcloud" && (
                                        <img
                                            src="./icons/soundcloud.svg"
                                            alt="SoundCloud"
                                            className="w-7 h-7 p-0.5 ml-3 mb-1 inline"
                                        />
                                    )}
                                </h1>
                                <div className="text-sm text-gray-600">
                                    {playlistInfo.last_synced
                                        ? `Last synced: ${new Date(playlistInfo.last_synced).toLocaleString()}`
                                        : 'Not synced'}
                                </div>
                                <div className="text-sm text-gray-600 mt-1">
                                    {playlistInfo.downloaded_track_count} downloaded / {playlistInfo.track_count} total tracks
                                </div>
                            </div>
                        </div>
                        {/* Right section: delete button */}
                        <div className="flex items-center space-x-4 mt-4 sm:mt-0">
                            <button onClick={handleDeleteClick} className="p-2 rounded bg-red-500 hover:bg-red-600 text-white">
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22m-5-4h-8m8 0a1 1 0 00-1-1h-6a1 1 0 00-1 1m8 0H5" />
                                </svg>
                            </button>
                        </div>
                    </div>
                ) : (
                    <h1 className="text-3xl font-semibold text-gray-700">Playlist ID: {playlistId}</h1>
                )}
            </div>

            {error ? (
                <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-400 rounded">
                    {error}
                </div>
            ) : (
                <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
                    <div id="track-table">
                        {tracks.length > 0 ? (
                            <ul>
                                {tracks.map((track, index) => (
                                    <li
                                        key={track.platform_id}
                                        className="flex px-4 py-1 bg-grey-100 border-y flex items-center cursor-pointer hover:bg-gray-50"
                                        onClick={() => setSelectedTrack(track)}
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
                                        <div className="flex flex-row text-sm flex-grow">
                                            <h2 className="font-semibold mr-2 hover:underline">
                                                <a
                                                    href={track.download_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    onClick={(e) => e.stopPropagation()}
                                                >
                                                    {track.name}
                                                </a>
                                            </h2>
                                            <p className="text-gray-600 mr-2">{track.artist}</p>
                                            {track.album && <p className="text-gray-500">{track.album}</p>}
                                        </div>
                                        <div className="flex flex-row items-end justify-end">
                                            {track.notes_errors && (
                                                    <img
                                                        src="./icons/warning.png"
                                                        alt="Warning"
                                                        title={`Error: ${track.notes_errors}`}
                                                        className="w-4 h-4 mx-1 inline"
                                                    />
                                                )}
                                            {track.download_location ? (
                                                <img
                                                    src="./icons/accept.png"
                                                    alt="Downloaded"
                                                    title='Downloaded'
                                                    className="w-4 h-4 ml-2 inline"
                                                />
                                            ) : (
                                                <p className="text-gray-700 text-xs mt-1">Not Yet Downloaded</p>
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
            )}

            {/* Render the modal if a track is selected */}
            {selectedTrack && (
                <TrackModal
                    track={selectedTrack}
                    onClose={() => setSelectedTrack(null)}
                    handleUpdateTrack={handleUpdateTrack}
                />
            )}
        </div>
    );
}

export default PlaylistPage;
