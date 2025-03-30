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
    const [trackLimit, setTrackLimit] = useState('');
    const [dateLimit, setDateLimit] = useState('');
    const [savedTrackLimit, setSavedTrackLimit] = useState('');
    const [savedDateLimit, setSavedDateLimit] = useState('');
    const navigate = useNavigate();

    const playlistInfo = playlists.find(pl => String(pl.id) === playlistId);

    // Set default limits from playlistInfo when available
    useEffect(() => {
        if (playlistInfo) {
            const defaultTrack = playlistInfo.track_limit ? String(playlistInfo.track_limit) : '';
            setTrackLimit(defaultTrack);
            setSavedTrackLimit(defaultTrack);

            // todo: extract to new to function
            if (playlistInfo.date_limit) {
                const d = new Date(playlistInfo.date_limit);
                const yyyy = d.getFullYear();
                const mm = String(d.getMonth() + 1).padStart(2, '0');
                const dd = String(d.getDate()).padStart(2, '0');
                const formattedDate = `${yyyy}-${mm}-${dd}`;
                setDateLimit(formattedDate);
                setSavedDateLimit(formattedDate);
            } else {
                setDateLimit('');
                setSavedDateLimit('');
            }
        }
    }, [playlistInfo]);

    // Fetch the playlist's tracks
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

    useEffect(() => {
        fetchPlaylistTracks();
    }, [playlistId]);

    // Save settings and refresh the track list
    const handleSaveSettings = async () => {
        const payload = {
            track_limit: trackLimit,
            date_limit: dateLimit,
        };

        try {
            const response = await fetch(`${backendUrl}/api/playlists/${playlistInfo.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (response.ok) {
                const updatedPlaylist = await response.json();
                const newTrackLimit = updatedPlaylist.track_limit ? String(updatedPlaylist.track_limit) : '';
                setSavedTrackLimit(newTrackLimit);
                setTrackLimit(newTrackLimit);
                if (updatedPlaylist.date_limit) {
                    const d = new Date(updatedPlaylist.date_limit);
                    const yyyy = d.getFullYear();
                    const mm = String(d.getMonth() + 1).padStart(2, '0');
                    const dd = String(d.getDate()).padStart(2, '0');
                    const formattedDate = `${yyyy}-${mm}-${dd}`;
                    setDateLimit(formattedDate);
                    setSavedDateLimit(formattedDate);
                } else {
                    setDateLimit('');
                    setSavedDateLimit('');
                }
                // After save, unsaved changes are gone.
                await fetchPlaylistTracks();
            } else {
                const errorData = await response.json();
                setError(errorData.error || 'Failed to update settings');
            }
        } catch (err) {
            console.error(err);
            setError('Error updating settings');
        }
    };

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

    // Update a track in state after a successful edit
    const handleUpdateTrack = (updatedTrack) => {
        setTracks(tracks.map(t => (t.id === updatedTrack.id ? updatedTrack : t)));
    };

    // Check for unsaved changes by comparing current inputs with saved values
    const hasUnsavedChanges =
        savedTrackLimit !== trackLimit || savedDateLimit !== dateLimit;

    return (
        <div id="playlist-page" className="flex flex-col h-screen p-4 pt-2">
            {/* Playlist Info Header with inline settings */}
            <div id="header-box" className="flex flex-col bg-white p-5 rounded-lg mb-1 shadow flex ">
                {playlistInfo ? (
                    <div>
                        <div className="flex flex-col sm:flex-row justify-between items-center justify-end w-full mb-6">
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
                                        {playlistInfo.downloaded_track_count} downloaded / {playlistInfo.tracks.length} total tracks
                                        {playlistInfo.tracks.length != playlistInfo.track_count ? (<a>, ({playlistInfo.track_count} total platform tracks)</a>) : (<a></a>)}
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

                        <div id='limit-tracks-settings' className="flex items-center space-x-4 border-t pt-4 text-sm">
                            {/* Track Limit Input */}
                            <label htmlFor="trackLimit" className=" text-gray-700">Track Limit</label>
                            <input
                                type="number"
                                id="trackLimit"
                                placeholder="None"
                                value={trackLimit}
                                onChange={(e) => setTrackLimit(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Escape') {
                                        setTrackLimit(savedTrackLimit);
                                    }
                                }}
                                className="mt-1 p-2 border rounded w-24 h-8"
                            />
                            {/* Date Limit Input */}
                            <label htmlFor="dateLimit" className="text-sm text-gray-700">Date Limit</label>
                            <input
                                type="date"
                                id="dateLimit"
                                value={dateLimit}
                                onChange={(e) => setDateLimit(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Escape') {
                                        setDateLimit(savedDateLimit);
                                    }
                                }}
                                className="mt-1 p-2 border rounded w-40 h-8"
                            />
                            {/* Save Button */}
                            <button
                                onClick={handleSaveSettings}
                                className="mt-1 p-2 rounded bg-blue-500 hover:bg-blue-600 text-white h-8 flex items-center justify-center"
                            >
                                {hasUnsavedChanges ? 'Save to take effect' : 'Save'}
                            </button>
                        </div>
                    </div>
                ) : (
                    <h1 className="text-3xl font-semibold text-gray-700">Playlist ID: {playlistId}</h1>
                )}
            </div>

            {/* Main Tracks Area */}
            {error ? (
                <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-400 rounded">
                    {error}
                </div>
            ) : (
                <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
                    <div id="track-table">
                        {tracks.length > 0 ? (
                            <ul>
                                {tracks.map((track, index) => {
                                    // Grey out tracks that would be removed:
                                    // - If track limit is set, tracks with an index >= limit are greyed out.
                                    // - If date limit is set and track.date_added exists, tracks with a date before the limit are greyed.
                                    const isGreyedOut =
                                        (trackLimit && index >= Number(trackLimit)) ||
                                        (dateLimit && track.date_added && new Date(track.date_added) < new Date(dateLimit));

                                    return (
                                        <li
                                            key={track.platform_id}
                                            className={`flex px-4 py-1 border-y flex items-center cursor-pointer hover:bg-gray-50 ${isGreyedOut ? 'opacity-50' : ''}`}
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
                                                        title="Downloaded"
                                                        className="w-4 h-4 ml-2 inline"
                                                    />
                                                ) : (
                                                    <p className="text-gray-700 text-xs mt-1">Not Yet Downloaded</p>
                                                )}
                                            </div>
                                        </li>
                                    );
                                })}
                            </ul>
                        ) : (
                            <div>No tracks found for this playlist.</div>
                        )}
                    </div>
                </div>
            )}

            {/* Track Modal */}
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
