import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTracklistById, useSaveTracklist, useUpdateTracklist, useDeleteTracklist, useRefreshTracklist, useDownloadTracklist } from '../hooks/useTracklists';
import TrackSearchModal from '../components/TrackSearchModal';
import { FaDownload } from 'react-icons/fa';
import { backendUrl } from '../config';

function TracklistDetailPage() {
    const { tracklistId } = useParams();
    const navigate = useNavigate();
    const { data: tracklist, isLoading, error } = useTracklistById(tracklistId);
    const saveMutation = useSaveTracklist();
    const updateMutation = useUpdateTracklist();
    const deleteMutation = useDeleteTracklist();
    const refreshMutation = useRefreshTracklist();
    const downloadMutation = useDownloadTracklist();

    const [localEntries, setLocalEntries] = useState([]);
    const [tracklistName, setTracklistName] = useState('');
    const [hasChanges, setHasChanges] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const [searchModalEntry, setSearchModalEntry] = useState(null);
    const [searchModalEntryIndex, setSearchModalEntryIndex] = useState(null);

    useEffect(() => {
        if (tracklist) {
            setLocalEntries(tracklist.tracklist_entries || tracklist.entries || []);
            setTracklistName(tracklist.set_name || tracklist.name || '');
        }
    }, [tracklist]);

    const handleConfirmTrack = async (entryIndex, trackId) => {
        const updatedEntries = [...localEntries];
        const currentEntry = updatedEntries[entryIndex];
        const isUnconfirming = currentEntry.confirmed_track_id === trackId;
        let confirmedTrack = null;

        if (!isUnconfirming) {
            if (currentEntry.confirmed_track && currentEntry.confirmed_track.id === trackId) {
                confirmedTrack = currentEntry.confirmed_track;
            } else if (currentEntry.predicted_track && currentEntry.predicted_track.id === trackId) {
                confirmedTrack = currentEntry.predicted_track;
            } else if (currentEntry.predicted_tracks && currentEntry.predicted_tracks.length > 0) {
                const match = currentEntry.predicted_tracks.find((prediction) => prediction.track && prediction.track.id === trackId);
                if (match) {
                    confirmedTrack = match.track;
                }
            }
        }

        updatedEntries[entryIndex] = {
            ...currentEntry,
            confirmed_track_id: isUnconfirming ? null : trackId,
            confirmed_track: isUnconfirming ? null : confirmedTrack,
        };
        setLocalEntries(updatedEntries);
        setHasChanges(true);
        await handleSave(updatedEntries);
    };

    const handleToggleFavourite = async (entryIndex) => {
        const updatedEntries = [...localEntries];
        const currentEntry = updatedEntries[entryIndex];
        updatedEntries[entryIndex] = {
            ...currentEntry,
            favourite: !currentEntry.favourite,
        };
        setLocalEntries(updatedEntries);
        setHasChanges(true);
        await handleSave(updatedEntries);
    };

    const handleSearchClick = (entry, entryIndex) => {
        setSearchModalEntry(entry);
        setSearchModalEntryIndex(entryIndex);
    };

    const handleCloseSearchModal = () => {
        setSearchModalEntry(null);
        setSearchModalEntryIndex(null);
    };

    const handleSelectTrack = async (selectedTrack, confidence) => {
        try {
            // Create or get the track in the database
            const response = await fetch(`${backendUrl}/api/tracks`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(selectedTrack),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to create track');
            }

            const track = await response.json();

            // Update the entry with the confirmed track
            const updatedEntries = [...localEntries];
            updatedEntries[searchModalEntryIndex] = {
                ...updatedEntries[searchModalEntryIndex],
                confirmed_track_id: track.id,
                confirmed_track: track,
                predicted_track_confidence: typeof confidence === 'number' ? confidence : updatedEntries[searchModalEntryIndex].predicted_track_confidence,
            };
            setLocalEntries(updatedEntries);
            setHasChanges(true);
            await handleSave(updatedEntries);

        } catch (error) {
            console.error('Error selecting track:', error);
            alert(`Failed to select track: ${error.message}`);
        }
    };

    const handleSave = async (entries = localEntries) => {
        const payload = {
            set_name: tracklistName || tracklist.set_name,
            artist: tracklist.artist,
            tracklist_string: tracklist.tracklist_string,
            folder_id: tracklist.folder_id || null,
            tracklist_entries: entries.map(entry => ({
                id: entry.id,
                predicted_track_id: entry.predicted_track_id,
                predicted_track_confidence: entry.predicted_track_confidence,
                confirmed_track_id: entry.confirmed_track_id,
                favourite: entry.favourite || false,
            }))
        };

        try {
            if (tracklist.id) {
                await updateMutation.mutateAsync({ id: tracklist.id, data: payload });
            } else {
                await saveMutation.mutateAsync(payload);
            }
            setHasChanges(false);
        } catch (error) {
            console.error('Error saving tracklist:', error);
        }
    };

    const handleDelete = async () => {
        if (!window.confirm('Are you sure you want to delete this tracklist?')) return;

        try {
            await deleteMutation.mutateAsync(tracklistId);
            navigate('/tracklists');
        } catch (error) {
            console.error('Error deleting tracklist:', error);
            alert(`Failed to delete tracklist: ${error.message}`);
        }
    };

    const handleRefreshClick = async () => {
        try {
            const refreshed = await refreshMutation.mutateAsync(tracklistId);
            if (refreshed?.tracklist_entries) {
                setLocalEntries(refreshed.tracklist_entries);
                setHasChanges(false);
            }
        } catch (error) {
            console.error('Error refreshing tracklist:', error);
        }
    };

    const getDownloadableTracks = (entries) => {
        const trackMap = new Map();
        entries.forEach((entry) => {
            const track = entry.confirmed_track;
            if (track && !track.download_location && !trackMap.has(track.id)) {
                trackMap.set(track.id, track);
            }
        });
        return Array.from(trackMap.values());
    };

    const handleDownloadTracklist = async () => {
        const tracksToDownload = getDownloadableTracks(localEntries);

        if (tracksToDownload.length === 0) {
            return;
        }

        setIsDownloading(true);

        try {
            const response = await downloadMutation.mutateAsync(tracklistId);
            if (response?.failed?.length > 0) {
                alert(`Failed to download ${response.failed.length} track(s). Check console for details.`);
            }
        } catch (error) {
            console.error('Error downloading tracklist:', error);
            alert(`Failed to download tracklist: ${error.message}`);
        } finally {
            setIsDownloading(false);
        }
    };

    const getConfidenceColor = (score) => {
        if (score >= 0.7) return 'text-green-600 bg-green-50';
        if (score >= 0.4) return 'text-yellow-600 bg-yellow-50';
        return 'text-red-600 bg-red-50';
    };

    const getConfidenceLabel = (score) => {
        if (score >= 0.7) return 'High';
        if (score >= 0.4) return 'Medium';
        return 'Low';
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-xl text-gray-600">Loading tracklist...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-xl text-red-600">Error: {error.message}</div>
            </div>
        );
    }

    if (!tracklist) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-xl text-gray-600">Tracklist not found</div>
            </div>
        );
    }

    const downloadCount = getDownloadableTracks(localEntries).length;

    return (
        <div className="flex flex-col h-screen p-4 pt-2">
            {/* Header */}
            <div className="bg-white p-5 rounded-lg mb-4 shadow">
                <div className="flex flex-wrap justify-between items-start gap-3">
                    <div className="flex-1 min-w-0">
                        <textarea
                            rows={2}
                            value={tracklistName}
                            onChange={(e) => {
                                setTracklistName(e.target.value);
                                setHasChanges(true);
                            }}
                            placeholder="Tracklist Name"
                            className="text-3xl font-semibold text-gray-800 mb-2 border-b-2 border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none w-full resize-none leading-tight"
                        />
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span>
                                {localEntries.filter(e => e.confirmed_track_id).length} confirmed / {localEntries.length} total tracks
                            </span>
                            {tracklist.created_at && (
                                <span>Created: {new Date(tracklist.created_at).toLocaleDateString()}</span>
                            )}
                        </div>
                    </div>
                    <div className="flex items-center space-x-2">
                        {downloadCount > 0 && (
                            <button
                                onClick={handleDownloadTracklist}
                                disabled={isDownloading}
                                className="flex items-center gap-2 px-3 py-2 rounded bg-green-600 hover:bg-green-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                                title={`Download ${downloadCount} track${downloadCount !== 1 ? 's' : ''}`}
                            >
                                <FaDownload className="w-4 h-4" />
                                {isDownloading ? 'Downloading...' : `Download (${downloadCount})`}
                            </button>
                        )}
                        <button
                            onClick={handleRefreshClick}
                            className="mr-1 p-2 rounded bg-gray-400 hover:bg-gray-500 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Refresh tracklist predictions"
                            disabled={refreshMutation.isPending}
                        >
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                className={`w-6 h-6 ${refreshMutation.isPending ? 'animate-spin-reverse' : ''}`}
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="white"
                                    strokeWidth="0"
                                    width="24"
                                    height="24"
                                    viewBox="0 0 24 24"
                                >
                                    <path d="M9 12l-4.463 4.969-4.537-4.969h3c0-4.97 4.03-9 9-9 2.395 0 4.565.942 6.179 2.468l-2.004 2.231c-1.081-1.05-2.553-1.699-4.175-1.699-3.309 0-6 2.691-6 6h3zm10.463-4.969l-4.463 4.969h3c0 3.309-2.691 6-6 6-1.623 0-3.094-.65-4.175-1.699l-2.004 2.231c1.613 1.526 3.784 2.468 6.179 2.468 4.97 0 9-4.03 9-9h3l-4.537-4.969z" />
                                </svg>
                            </svg>
                        </button>
                        <button
                            onClick={handleDelete}
                            disabled={deleteMutation.isPending}
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
                </div>
            </div>

            {/* Entries List */}
            <div className="bg-white rounded-lg shadow overflow-hidden flex-1 flex flex-col">
                <div className="overflow-y-auto flex-1 ">
                    {localEntries.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <p className="text-lg">No entries in this tracklist</p>
                        </div>
                    ) : (
                        <table className="w-full">
                            <thead className="bg-gray-100 sticky top-0">
                                <tr>
                                    {/* <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider w-12">

                                    </th> */}
                                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase tracking-wider w-16">
                                        Favorite
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                                        Artist
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                                        Track Title
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                                        Version
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                                        Suggested Track
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider w-32">
                                        Confidence
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider w-24">
                                        Status
                                    </th>
                                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase tracking-wider w-20">
                                        Search
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {localEntries.map((entry, index) => (
                                    <tr key={entry.id || index} className="hover:bg-gray-50 h-16 align-middle">
                                        <td className="px-4 py-3 text-center h-16 align-middle">
                                            <button
                                                onClick={() => handleToggleFavourite(index)}
                                                className="focus:outline-none transition-colors"
                                                title={entry.favourite ? 'Remove from favourites' : 'Add to favourites'}
                                            >
                                                <svg
                                                    width="20"
                                                    height="20"
                                                    viewBox="0 0 24 24"
                                                    fill={entry.favourite ? '#ef4444' : 'none'}
                                                    stroke={entry.favourite ? '#ef4444' : '#9ca3af'}
                                                    strokeWidth="2"
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                >
                                                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                                                </svg>
                                            </button>
                                        </td>
                                        {/* <td className="px-4 py-3 text-sm text-gray-900">
                                            {entry.position}
                                        </td> */}
                                        <td className="px-4 py-3 text-sm text-gray-900">
                                            {entry.artist || <span className="text-gray-400 italic">Unknown</span>}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-900">
                                            {entry.short_title || entry.full_title || entry.track_title || <span className="text-gray-400 italic">Unknown</span>}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-900">
                                            {entry.version || <span className="text-gray-400 italic">—</span>}
                                        </td>
                                        <td className="flex justify-between items-center px-4 py-3 text-sm">

                                            {(() => {
                                                const track = entry.confirmed_track
                                                    || entry.predicted_track
                                                    || (entry.predicted_tracks && entry.predicted_tracks.length > 0 ? entry.predicted_tracks[0].track : null);

                                                return track ? (
                                                    <div className="flex items-center space-x-3">
                                                        {track.album_art_url && (
                                                            <img
                                                                src={track.album_art_url}
                                                                alt={track.name}
                                                                className="w-10 h-10 rounded object-cover"
                                                            />
                                                        )}
                                                        <div className="flex flex-col">
                                                            <span className="font-medium text-gray-900">
                                                                {track.name}
                                                            </span>
                                                            <span className="text-xs text-gray-500">
                                                                {track.artist}
                                                            </span>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <span className="text-gray-400 italic">No match found</span>
                                                );
                                            })()}
                                            {entry.confirmed_track && !entry.confirmed_track.download_location && (
                                                <FaDownload className="ml-2 text-gray-500" title="No download location" />
                                            )}
                                        </td>

                                        <td className="px-4 py-3">
                                            {(() => {
                                                // Prefer entry.predicted_track.confidence if present, else fallback to predicted_tracks[0]?.confidence
                                                let confidence = null;
                                                if (typeof entry.predicted_track_confidence === 'number') {
                                                    confidence = entry.predicted_track_confidence;
                                                } else if (entry.predicted_track && typeof entry.predicted_track.confidence === 'number') {
                                                    confidence = entry.predicted_track.confidence;
                                                } else if (entry.predicted_tracks && entry.predicted_tracks.length > 0 && typeof entry.predicted_tracks[0].confidence === 'number') {
                                                    confidence = entry.predicted_tracks[0].confidence;
                                                }
                                                return confidence != null ? (
                                                    <div className="flex items-center space-x-2">
                                                        <span className={`px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(confidence)}`}>
                                                            {getConfidenceLabel(confidence)}
                                                        </span>
                                                        <span className="text-xs text-gray-600">
                                                            {Math.round(confidence * 100)}%
                                                        </span>
                                                    </div>
                                                ) : (
                                                    <span className="text-gray-400 text-xs italic ">-</span>
                                                );
                                            })()}
                                        </td>
                                        <td className="px-4 py-3">
                                            {(() => {
                                                const topPrediction = entry.predicted_tracks && entry.predicted_tracks.length > 0
                                                    ? entry.predicted_tracks[0]
                                                    : null;
                                                const predictedTrackId = entry.predicted_track_id || topPrediction?.track?.id;

                                                return entry.confirmed_track_id ? (
                                                    <button
                                                        onClick={() => handleConfirmTrack(index, entry.confirmed_track_id)}
                                                        className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium hover:bg-green-200 transition-colors"
                                                        title="Click to unconfirm"
                                                    >
                                                        Confirmed
                                                    </button>
                                                ) : predictedTrackId ? (
                                                    <button
                                                        onClick={() => handleConfirmTrack(index, predictedTrackId)}
                                                        className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium hover:bg-blue-200 transition-colors"
                                                    >
                                                        Confirm
                                                    </button>
                                                ) : (
                                                    <span >

                                                    </span>
                                                );
                                            })()}
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            <button
                                                onClick={() => handleSearchClick(entry, index)}
                                                className={`p-1 rounded transition-colors ${entry.id ? 'hover:bg-blue-100' : 'opacity-40 cursor-not-allowed'}`}
                                                title={entry.id ? 'Search for track' : 'Save tracklist first to enable search'}
                                                disabled={!entry.id}
                                            >
                                                <svg
                                                    xmlns="http://www.w3.org/2000/svg"
                                                    className="w-5 h-5 text-blue-600"
                                                    fill="none"
                                                    viewBox="0 0 24 24"
                                                    stroke="currentColor"
                                                >
                                                    <path
                                                        strokeLinecap="round"
                                                        strokeLinejoin="round"
                                                        strokeWidth={2}
                                                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                                                    />
                                                </svg>
                                            </button>
                                        </td>

                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {/* Track Search Modal */}
            {
                searchModalEntry && (
                    <TrackSearchModal
                        entry={searchModalEntry}
                        onClose={handleCloseSearchModal}
                        onSelectTrack={handleSelectTrack}
                    />
                )
            }
        </div >
    );
}

export default TracklistDetailPage;
