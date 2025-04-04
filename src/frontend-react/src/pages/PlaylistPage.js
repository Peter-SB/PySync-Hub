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
    const [isLimitsOpen, setIsLimitsOpen] = useState(false);

    const navigate = useNavigate();

    const playlistInfo = playlists.find(pl => String(pl.id) === playlistId);

    useEffect(() => {
        if (playlistInfo) {
            const defaultTrack = playlistInfo.track_limit ? String(playlistInfo.track_limit) : '';
            setTrackLimit(defaultTrack);
            setSavedTrackLimit(defaultTrack);

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

    // Refresh playlist info and tracks without downloading
    const handleRefreshClick = async () => {
        try {
            const response = await fetch(`${backendUrl}/api/playlists/${playlistId}/refresh`, {
                method: 'POST',
            });
            if (!response.ok) {
                console.error('Failed to refresh playlist');
            }
            fetchPlaylistTracks()
        } catch (error) {
            console.error('Error refreshing playlist', error);
        }
    };

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

    const handleSaveSettings = async () => {
        const payload = {
            track_limit: trackLimit ? parseInt(trackLimit, 10) : null,
            date_limit: dateLimit || null,
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
            } else {
                const errorData = await response.json();
                setError(errorData.error || 'Failed to update settings');
            }
            handleRefreshClick();
        } catch (err) {
            console.error(err);
            setError('Error updating settings and refreshing playlist');
        }
    };

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

    const handleUpdateTrack = (updatedTrack) => {
        setTracks(tracks.map(t => (t.id === updatedTrack.id ? updatedTrack : t)));
    };

    const hasUnsavedChanges =
        savedTrackLimit !== trackLimit || savedDateLimit !== dateLimit;

    return (
        <div id="playlist-page" className="flex flex-col h-screen p-4 pt-2">
            <div id="header-box" className="flex flex-col bg-white p-5 rounded-lg mb-1 shadow flex ">
                {playlistInfo ? (
                    <div>
                        <div className="flex flex-col sm:flex-row justify-between items-center w-full h-[100px]">
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
                                        <a
                                            href={playlistInfo.url}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="hover:underline"
                                        >
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
                                        {playlistInfo.tracks.length !== playlistInfo.track_count ? (
                                            <>, ({playlistInfo.track_count} total platform tracks)</>
                                        ) : null}
                                    </div>
                                </div>
                            </div>
                            <div className="flex flex-col justify-between h-full justify-end">
                                <div className="flex-1 flex items-center justify-end space-x-1 mt-0">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleRefreshClick();
                                        }}
                                        className="mr-1 p-2 rounded bg-gray-400 hover:bg-gray-500 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                                        title="Refresh playlist and tracks without downloading"
                                    >
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            className="w-6 h-6"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                        >
                                            <svg
                                                xmlns="http://www.w3.org/2000/svg"
                                                fill='white'
                                                strokeWidth="0"
                                                width="24"
                                                height="24"
                                                viewBox="0 0 24 24">
                                                <path d="M9 12l-4.463 4.969-4.537-4.969h3c0-4.97 4.03-9 9-9 2.395 0 4.565.942 6.179 2.468l-2.004 2.231c-1.081-1.05-2.553-1.699-4.175-1.699-3.309 0-6 2.691-6 6h3zm10.463-4.969l-4.463 4.969h3c0 3.309-2.691 6-6 6-1.623 0-3.094-.65-4.175-1.699l-2.004 2.231c1.613 1.526 3.784 2.468 6.179 2.468 4.97 0 9-4.03 9-9h3l-4.537-4.969z" />
                                            </svg>
                                        </svg>
                                    </button>
                                    <button
                                        onClick={handleDeleteClick}
                                        className="p-2 rounded bg-red-500 hover:bg-red-600 text-white"
                                        title="Delete"
                                    >
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            className="w-6 h-6"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                strokeWidth={2}
                                                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22m-5-4h-8m8 0a1 1 0 00-1-1h-6a1 1 0 00-1 1m8 0H5"
                                            />
                                        </svg>
                                    </button>
                                </div>
                                <div className='flex justify-end'>
                                    <button
                                        className="flex items-center space-x-1 opacity-50"
                                        onClick={() => setIsLimitsOpen(!isLimitsOpen)}
                                    >
                                        <span className="text-xs">Options</span>
                                        <svg
                                            className={`w-5 h-5 transform transition-transform ${!isLimitsOpen ? 'rotate-180' : 'rotate-0'
                                                }`}
                                            fill="none"
                                            stroke="currentColor"
                                            strokeWidth="2"
                                            viewBox="0 0 24 24"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                d="M5 15l7-7 7 7"
                                            />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>

                        {isLimitsOpen && (
                            <div
                                id="limit-tracks-settings"
                                className="flex items-center justify-end space-x-4 border-t pt-4 text-xs mt-6"
                            >
                                <label htmlFor="trackLimit" className="text-gray-700">
                                    Track Limit
                                </label>
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
                                    className="mt-1 p-2 border rounded w-16 h-6"
                                />

                                {playlistInfo.platform === "spotify" && (
                                    <div>
                                        <label htmlFor="dateLimit" className="text-gray-700">
                                            Date Limit{' '}
                                        </label>
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
                                            className="mt-1 p-2 border rounded w-30 h-6"
                                        />
                                    </div>
                                )}

                                <button
                                    onClick={handleSaveSettings}
                                    className="mt-1 p-2 rounded bg-blue-500 hover:bg-blue-600 text-white h-7 flex items-center justify-center"
                                >
                                    {hasUnsavedChanges ? 'Save to take effect' : 'Save'}
                                </button>
                            </div>
                        )}
                    </div>
                ) : (
                    <h1 className="text-3xl font-semibold text-gray-700">
                        Playlist ID: {playlistId}
                    </h1>
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
                                {tracks.map((track, index) => {
                                    const isGreyedOut =
                                        (trackLimit && index >= Number(trackLimit)) ||
                                        (dateLimit && track.added_on && new Date(track.added_on) < new Date(dateLimit));

                                    return (
                                        <li
                                            key={track.platform_id}
                                            className={`flex px-4 py-1 border-y flex items-center cursor-pointer hover:bg-gray-50 ${isGreyedOut ? 'opacity-50' : ''
                                                }`}
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
