import React, { useState, useEffect } from 'react';
import { useSearchTracks } from '../hooks/useTracklists';

const TrackSearchModal = ({ entry, onClose, onSelectTrack }) => {
    const [results, setResults] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const searchMutation = useSearchTracks();

    useEffect(() => {
        // Perform search when modal opens
        const performSearch = async () => {
            setIsLoading(true);
            try {
                // Build search query from entry: Artist - Title - Version
                const queryParts = [];
                if (entry.artist) queryParts.push(entry.artist);
                if (entry.short_title || entry.track_title) queryParts.push(entry.short_title || entry.track_title);
                if (entry.version) queryParts.push(entry.version);

                const query = queryParts.join(' - ');

                const searchResults = await searchMutation.mutateAsync({ query, limit: 3 });
                setResults(searchResults || []);
            } catch (error) {
                console.error('Error searching for tracks:', error);
                setResults([]);
            } finally {
                setIsLoading(false);
            }
        };

        performSearch();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [entry]);

    const handleTrackSelect = (track) => {
        onSelectTrack(track);
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
                    <div className="text-gray-600"> Track Search Results </div>
                </div>

                {/* Results */}
                <div className="flex-1 overflow-y-auto">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                        </div>
                    ) : results.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            <p className="text-lg">No results found</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {results.map((track, index) => (
                                <div
                                    key={`${track.platform}-${track.platform_id}-${index}`}
                                    onClick={() => handleTrackSelect(track)}
                                    className="flex items-center p-4 border rounded-lg hover:bg-blue-50 cursor-pointer transition-colors"
                                >
                                    {/* Album Art */}
                                    {track.album_art_url && (
                                        <img
                                            src={track.album_art_url}
                                            alt={track.name}
                                            className="w-16 h-16 rounded object-cover mr-4"
                                        />
                                    )}

                                    {/* Track Info */}
                                    <div className="flex-1">
                                        <div className="font-medium text-gray-900">{track.name}</div>
                                        <div className="text-sm text-gray-600">{track.artist}</div>
                                        {track.album && (
                                            <div className="text-xs text-gray-500">{track.album}</div>
                                        )}
                                    </div>

                                    {/* Platform Icon */}
                                    <div className="ml-4">
                                        {getPlatformIcon(track.platform)}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Close Button */}
                <div className="mt-4 pt-4 border-t flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default TrackSearchModal;
