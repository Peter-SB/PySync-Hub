import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTracklistById, useSaveTracklist, useUpdateTracklist, useDeleteTracklist } from '../hooks/useTracklists';

function TracklistDetailPage() {
    const { tracklistId } = useParams();
    const navigate = useNavigate();
    const { data: tracklist, isLoading, error } = useTracklistById(tracklistId);
    const saveMutation = useSaveTracklist();
    const updateMutation = useUpdateTracklist();
    const deleteMutation = useDeleteTracklist();

    const [localEntries, setLocalEntries] = useState([]);
    const [tracklistName, setTracklistName] = useState('');
    const [hasChanges, setHasChanges] = useState(false);

    useEffect(() => {
        if (tracklist) {
            setLocalEntries(tracklist.tracklist_entries || tracklist.entries || []);
            setTracklistName(tracklist.set_name || tracklist.name || '');
        }
    }, [tracklist]);

    const handleConfirmTrack = (entryIndex, trackId) => {
        const updatedEntries = [...localEntries];
        updatedEntries[entryIndex] = {
            ...updatedEntries[entryIndex],
            confirmed_track_id: trackId,
        };
        setLocalEntries(updatedEntries);
        setHasChanges(true);
    };

    const handleSave = async () => {
        const payload = {
            id: tracklist.id,
            name: tracklistName || undefined,
            folder_id: tracklist.folder_id || null,
            entries: localEntries.map(entry => ({
                id: entry.id,
                position: entry.position,
                raw_text: entry.full_tracklist_entry || entry.raw_text,
                artist: entry.artist,
                track_title: entry.short_title || entry.full_title || entry.track_title,
                predicted_track_id: entry.predicted_track_id,
                confirmed_track_id: entry.confirmed_track_id,
                confidence_score: entry.confidence_score,
            }))
        };

        try {
            if (tracklist.id) {
                await updateMutation.mutateAsync({ id: tracklist.id, data: payload });
            } else {
                await saveMutation.mutateAsync(payload);
            }
            setHasChanges(false);
            alert('Tracklist saved successfully!');
        } catch (error) {
            console.error('Error saving tracklist:', error);
            alert(`Failed to save tracklist: ${error.message}`);
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

    const getConfidenceColor = (score) => {
        if (score >= 0.8) return 'text-green-600 bg-green-50';
        if (score >= 0.5) return 'text-yellow-600 bg-yellow-50';
        return 'text-red-600 bg-red-50';
    };

    const getConfidenceLabel = (score) => {
        if (score >= 0.8) return 'High';
        if (score >= 0.5) return 'Medium';
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

    return (
        <div className="flex flex-col h-screen p-4 pt-2">
            {/* Header */}
            <div className="bg-white p-5 rounded-lg mb-4 shadow">
                <div className="flex justify-between items-start">
                    <div className="flex-1">
                        <input
                            type="text"
                            value={tracklistName}
                            onChange={(e) => {
                                setTracklistName(e.target.value);
                                setHasChanges(true);
                            }}
                            placeholder="Tracklist Name"
                            className="text-3xl font-semibold text-gray-800 mb-2 border-b-2 border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none w-full"
                        />
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span>{localEntries.length} entries</span>
                            {tracklist.created_at && (
                                <span>Created: {new Date(tracklist.created_at).toLocaleDateString()}</span>
                            )}
                            {hasChanges && (
                                <span className="text-orange-600 font-medium">● Unsaved changes</span>
                            )}
                        </div>
                    </div>
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={handleSave}
                            disabled={!hasChanges || saveMutation.isPending || updateMutation.isPending}
                            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {(saveMutation.isPending || updateMutation.isPending) ? 'Saving...' : 'Save'}
                        </button>
                        <button
                            onClick={handleDelete}
                            disabled={deleteMutation.isPending}
                            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 transition-colors"
                        >
                            Delete
                        </button>
                    </div>
                </div>
            </div>

            {/* Entries List */}
            <div className="bg-white rounded-lg shadow overflow-hidden flex-1 flex flex-col">
                <div className="overflow-y-auto flex-1">
                    {localEntries.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <p className="text-lg">No entries in this tracklist</p>
                        </div>
                    ) : (
                        <table className="w-full">
                            <thead className="bg-gray-100 sticky top-0">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider w-12">
                                        #
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                                        Artist
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                                        Track Title
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
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {localEntries.map((entry, index) => (
                                    <tr key={entry.id || index} className="hover:bg-gray-50">
                                        <td className="px-4 py-3 text-sm text-gray-900">
                                            {entry.position}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-900">
                                            {entry.artist || <span className="text-gray-400 italic">Unknown</span>}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-900">
                                            {entry.short_title || entry.full_title || entry.track_title || <span className="text-gray-400 italic">Unknown</span>}
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            {(() => {
                                                const topPrediction = entry.predicted_tracks && entry.predicted_tracks.length > 0
                                                    ? entry.predicted_tracks[0]
                                                    : null;
                                                const track = topPrediction?.track;

                                                return track ? (
                                                    <div className="flex flex-col">
                                                        <span className="font-medium text-gray-900">
                                                            {track.name}
                                                        </span>
                                                        <span className="text-xs text-gray-500">
                                                            {track.artist}
                                                        </span>
                                                    </div>
                                                ) : (
                                                    <span className="text-gray-400 italic">No match found</span>
                                                );
                                            })()}
                                        </td>
                                        <td className="px-4 py-3">
                                            {(() => {
                                                const topPrediction = entry.predicted_tracks && entry.predicted_tracks.length > 0
                                                    ? entry.predicted_tracks[0]
                                                    : null;
                                                const confidence = topPrediction?.confidence;

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
                                                    <span className="text-gray-400 text-xs italic">N/A</span>
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
                                                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
                                                        Confirmed
                                                    </span>
                                                ) : predictedTrackId ? (
                                                    <button
                                                        onClick={() => handleConfirmTrack(index, predictedTrackId)}
                                                        className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium hover:bg-blue-200 transition-colors"
                                                    >
                                                        Confirm
                                                    </button>
                                                ) : (
                                                    <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-medium">
                                                        No Match
                                                    </span>
                                                );
                                            })()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}

export default TracklistDetailPage;
