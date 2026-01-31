import React, { useState } from 'react';
import { useSaveTracklist } from '../hooks/useTracklists';

function TracklistPreviewModal({ data, onClose, onSaved }) {
    const [localEntries, setLocalEntries] = useState(data.tracklist_entries || []);
    const [tracklistName, setTracklistName] = useState(data.set_name || '');
    const saveMutation = useSaveTracklist();

    const handleConfirmTrack = (entryIndex, trackId) => {
        const updatedEntries = [...localEntries];
        updatedEntries[entryIndex] = {
            ...updatedEntries[entryIndex],
            confirmed_track_id: trackId,
        };
        setLocalEntries(updatedEntries);
    };

    const handleSave = async () => {
        const payload = {
            set_name: tracklistName || data.set_name,
            artist: data.artist,
            tracklist_string: data.tracklist_string,
            rating: data.rating,
            image_url: data.image_url,
            folder_id: data.folder_id,
            tracklist_entries: localEntries.map((entry, index) => ({
                position: index + 1,
                raw_text: entry.full_tracklist_entry,
                artist: entry.artist,
                track_title: entry.short_title || entry.full_title,
                predicted_track_id: entry.predicted_track_id || (entry.predicted_tracks && entry.predicted_tracks[0]?.track?.id),
                confirmed_track_id: entry.confirmed_track_id,
            }))
        };

        try {
            const savedTracklist = await saveMutation.mutateAsync(payload);
            if (savedTracklist && savedTracklist.id) {
                onSaved(savedTracklist.id);
            } else {
                alert('Tracklist saved but no ID returned');
                onClose();
            }
        } catch (error) {
            console.error('Error saving tracklist:', error);
            alert(`Failed to save tracklist: ${error.message}`);
        }
    };

    const getConfidenceColor = (score) => {
        if (score >= 0.75) return 'text-green-600 bg-green-50';
        if (score >= 0.5) return 'text-yellow-600 bg-yellow-50';
        return 'text-red-600 bg-red-50';
    };

    const getConfidenceLabel = (score) => {
        if (score >= 0.75) return 'High';
        if (score >= 0.5) return 'Medium';
        return 'Low';
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-7xl max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="flex justify-between items-start p-6 border-b">
                    <div className="flex-1">
                        <input
                            type="text"
                            value={tracklistName}
                            onChange={(e) => setTracklistName(e.target.value)}
                            placeholder="Tracklist Name"
                            className="text-3xl font-semibold text-gray-800 mb-2 border-b-2 border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none w-full"
                        />
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span>{localEntries.length} entries</span>
                            <span className="text-blue-600 font-medium">● Preview - Not Saved</span>
                        </div>
                    </div>
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={handleSave}
                            disabled={saveMutation.isPending}
                            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {saveMutation.isPending ? 'Saving...' : 'Save Tracklist'}
                        </button>
                        <button
                            onClick={onClose}
                            disabled={saveMutation.isPending}
                            className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 disabled:opacity-50 transition-colors"
                        >
                            Cancel
                        </button>
                    </div>
                </div>

                {/* Entries Table */}
                <div className="flex-1 overflow-y-auto p-6">
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
                                {localEntries.map((entry, index) => {
                                    const topPrediction = entry.predicted_tracks && entry.predicted_tracks.length > 0
                                        ? entry.predicted_tracks[0]
                                        : null;
                                    const track = topPrediction?.track;
                                    const confidence = topPrediction?.confidence;
                                    const predictedTrackId = entry.predicted_track_id || track?.id;

                                    return (
                                        <tr key={index} className="hover:bg-gray-50">
                                            <td className="px-4 py-3 text-sm text-gray-900">
                                                {index + 1}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-gray-900">
                                                {entry.artist || <span className="text-gray-400 italic">Unknown</span>}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-gray-900">
                                                {entry.short_title || entry.full_title || <span className="text-gray-400 italic">Unknown</span>}
                                            </td>
                                            <td className="px-4 py-3 text-sm">
                                                {track ? (
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
                                                )}
                                            </td>
                                            <td className="px-4 py-3">
                                                {confidence != null ? (
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
                                                )}
                                            </td>
                                            <td className="px-4 py-3">
                                                {entry.confirmed_track_id ? (
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
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}

export default TracklistPreviewModal;
