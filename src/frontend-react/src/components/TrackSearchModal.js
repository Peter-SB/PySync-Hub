import React, { useState, useEffect } from 'react';
import { useResolveTrackUrl, useSearchTracks } from '../hooks/useTracklists';

const SEARCH_RESULTS_CONFIDENCE_THRESHOLD = 0.1;
const SEARCH_RESULTS_LIMIT = 2;

const TrackSearchModal = ({ entry, onClose, onSelectTrack }) => {
    const [results, setResults] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');
    const [urlInput, setUrlInput] = useState('');
    const [urlError, setUrlError] = useState('');
    const [isResolvingUrl, setIsResolvingUrl] = useState(false);
    const [showAllResults, setShowAllResults] = useState(false);
    const searchMutation = useSearchTracks();
    const resolveUrlMutation = useResolveTrackUrl();

    const formatDuration = (durationMs) => {
        if (typeof durationMs !== 'number' || Number.isNaN(durationMs)) {
            return null;
        }
        const totalSeconds = Math.floor(durationMs / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    };

    const getConfidenceLabel = (score) => {
        if (score >= 0.7) return 'High';
        if (score >= 0.4) return 'Medium';
        return 'Low';
    };

    const getConfidenceClass = (score) => {
        if (score >= 0.7) return 'bg-green-100 text-green-700';
        if (score >= 0.4) return 'bg-yellow-100 text-yellow-700';
        return 'bg-red-100 text-red-700';
    };

    useEffect(() => {
        const performSearch = async () => {
            setIsLoading(true);
            setErrorMessage('');
            try {
                if (!entry?.id) {
                    setResults([]);
                    setErrorMessage('Missing tracklist entry ID.');
                    return;
                }

                const response = await searchMutation.mutateAsync({ entryId: entry.id, limit: SEARCH_RESULTS_LIMIT });
                const predicted = response?.predicted_tracks || [];
                setResults(predicted);
            } catch (error) {
                console.error('Error searching for tracks:', error);
                setResults([]);
                setErrorMessage('Search failed.');
            } finally {
                setIsLoading(false);
            }
        };

        performSearch();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [entry]);

    const handleTrackSelect = (track, confidence) => {
        onSelectTrack(track, confidence);
        onClose();
    };

    const getPlatformIcon = (platform) => {
        const icons = {
            spotify: (
                <img
                    src="/icons/spotify.svg"
                    alt="Spotify"
                    className="w-6 h-6"
                />
            ),
            youtube: (
                <img
                    src="/icons/youtube.svg"
                    alt="YouTube"
                    className="w-6 h-6"
                />
            ),
            soundcloud: (
                <img
                    src="/icons/soundcloud.svg"
                    alt="SoundCloud"
                    className="w-6 h-6"
                />
            ),
        };
        return icons[platform] || null;
    };

    const handleAddFromUrl = async () => {
        const url = urlInput.trim();
        if (!url) {
            setUrlError('Enter a URL.');
            return;
        }
        if (!entry?.id) {
            setUrlError('Missing tracklist entry ID.');
            return;
        }

        setUrlError('');
        setIsResolvingUrl(true);
        try {
            const response = await resolveUrlMutation.mutateAsync({ entryId: entry.id, url });
            if (!response?.track) {
                setUrlError('No track found for that URL.');
                return;
            }

            handleTrackSelect(response.track, response.confidence);
            setUrlInput('');
        } catch (error) {
            console.error('Error resolving track URL:', error);
            setUrlError(error?.message || 'Failed to resolve URL.');
        } finally {
            setIsResolvingUrl(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
            <div
                className="bg-white rounded-lg shadow-lg p-6 w-3/5 max-h-[80vh] flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="mb-4 pb-4 border-b">
                    <h2 className="text-2xl font-semibold text-gray-800 mb-2">
                        <span className="font-medium">{entry.artist || 'Unknown Artist'}</span>
                        {' - '}
                        <span>{entry.short_title || entry.track_title || 'Unknown Title'}</span>
                        {entry.version && (
                            <>
                                {' - '}
                                <span className="">{entry.version}</span>
                            </>
                        )}
                    </h2>
                    <div className="flex items-center justify-between text-gray-600">
                        <div>Track Search Results</div>
                        <label className="flex items-center gap-2 text-sm select-none">
                            <span>Show all results</span>
                            <input
                                type="checkbox"
                                className="h-4 w-4 accent-blue-600"
                                checked={showAllResults}
                                onChange={(e) => setShowAllResults(e.target.checked)}
                            />
                        </label>
                    </div>
                </div>

                {/* Results */}
                <div className="flex-1 overflow-y-auto">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                        </div>
                    ) : results.length === 0 ? (
                        <div className="text-center py-10 text-gray-500 text-sm">
                            <p>{errorMessage || 'No results found'}</p>
                        </div>
                    ) : (
                        <div className="space-y-1.5">
                            {results.filter((result) => {
                                if (showAllResults) {
                                    return true;
                                }
                                if (result?.source === 'url') {
                                    return true;
                                }
                                if (typeof result?.confidence === 'number') {
                                    return result.confidence >= SEARCH_RESULTS_CONFIDENCE_THRESHOLD;
                                }
                                return true;
                            }).map((result, index) => {
                                const track = result?.track || result;
                                const confidence = typeof result?.confidence === 'number' ? result.confidence : null;
                                const confidencePct = confidence != null ? Math.round(confidence * 100) : null;
                                const durationLabel = formatDuration(track?.duration_ms);
                                return (
                                    <div
                                        key={`${track.platform}-${track.platform_id}-${index}`}
                                        onClick={() => handleTrackSelect(track, confidence)}
                                        className="flex items-center p-2 border rounded-lg hover:bg-blue-50 cursor-pointer transition-colors"
                                    >
                                        {/* Platform */}
                                        <div className="mr-3 w-10 flex items-center justify-center">
                                            {getPlatformIcon(track.platform)}
                                        </div>

                                        {/* Album Art */}
                                        {track.album_art_url && (
                                            <img
                                                src={track.album_art_url}
                                                alt={track.name}
                                                className="w-10 h-10 rounded object-cover mr-3"
                                            />
                                        )}

                                        {/* Title / Artist */}
                                        <div className="flex-1">
                                            <div className="font-medium text-gray-900 text-sm">{track.name}</div>
                                            <div className="text-xs text-gray-600">{track.artist}  -  Length {durationLabel}</div>
                                        </div>

                                        {/* Confidence */}
                                        <div className="mr-3 text-right min-w-[200px]">
                                            {confidencePct != null ? (
                                                <div className="flex items-center justify-end gap-2">
                                                    <div className="text-right">
                                                        <div className="text-xs font-medium text-gray-700">{confidencePct}%</div>
                                                        <div className="text-[10px] text-gray-500">Confidence</div>
                                                    </div>
                                                    <span className='w-16 text-center'>
                                                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${getConfidenceClass(confidence)}`}>
                                                            {getConfidenceLabel(confidence)}
                                                        </span>
                                                    </span>
                                                </div>
                                            ) : (
                                                <div className="text-[11px] text-gray-400">—</div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Add From URL + Close */}
                <div className="mt-4 pt-4 border-t flex items-center gap-3">
                    <div className="flex-1 flex items-center gap-2">
                        <input
                            type="text"
                            value={urlInput}
                            onChange={(e) => setUrlInput(e.target.value)}
                            placeholder="Add from URL (Spotify, SoundCloud, YouTube)"
                            className="flex-1 px-3 py-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            disabled={isResolvingUrl}
                        />
                        <button
                            onClick={handleAddFromUrl}
                            className="px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            disabled={isResolvingUrl}
                        >
                            {isResolvingUrl ? 'Adding...' : 'Add from URL'}
                        </button>
                    </div>
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                    >
                        Close
                    </button>
                </div>
                {urlError && (
                    <div className="mt-2 text-sm text-red-600">
                        {urlError}
                    </div>
                )}
            </div>
        </div>
    );
};

export default TrackSearchModal;
