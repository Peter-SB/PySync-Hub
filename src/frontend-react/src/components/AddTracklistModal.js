import React, { useState } from 'react';
import { useProcessTracklist } from '../hooks/useTracklists';

function AddTracklistModal({ onClose, onSuccess }) {
    const [tracklistString, setTracklistString] = useState('');
    const [name, setName] = useState('');
    const [isArtistFirst, setIsArtistFirst] = useState(true);
    const processMutation = useProcessTracklist();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!tracklistString.trim()) return;

        const payload = {
            tracklist_string: tracklistString,
            set_name: name.trim() || undefined,
            artist_first: isArtistFirst,
        };

        processMutation.mutate(payload, {
            onSuccess: (data) => {
                // The backend returns the processed tracklist (without ID since it's not saved yet)
                // Pass the entire data object to parent to handle navigation
                if (data) {
                    onSuccess(data);
                } else {
                    onClose();
                }
            },
            onError: (error) => {
                console.error('Error processing tracklist:', error);
                alert(`Failed to process tracklist: ${error.message}`);
            }
        });
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className={`bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col relative ${processMutation.isPending ? 'opacity-60' : ''}`}>
                {/* Loading Overlay */}
                {processMutation.isPending && (
                    <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10 rounded-lg">
                        <div className="flex flex-col items-center">
                            <svg
                                className="animate-spin h-16 w-16 text-blue-600"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 24 24"
                            >
                                <circle
                                    className="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                ></circle>
                                <path
                                    className="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                ></path>
                            </svg>
                            <p className="mt-4 text-lg font-medium text-gray-700">Processing tracklist...</p>
                        </div>
                    </div>
                )}

                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b">
                    <h2 className="text-2xl font-semibold text-gray-800">Add Tracklist</h2>
                    <button
                        onClick={onClose}
                        className="text-gray-500 hover:text-gray-700 text-3xl leading-none"
                        disabled={processMutation.isPending}
                    >
                        &times;
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
                    <div className="flex-1 overflow-y-auto p-6 space-y-4">
                        {/* Name Input */}
                        <div>
                            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                                Tracklist Name (Optional)
                            </label>
                            <input
                                type="text"
                                id="name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="e.g., Boiler Room 2024"
                                className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                disabled={processMutation.isPending}
                            />
                        </div>

                        {/* Format Toggle */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Track Format
                            </label>
                            <div className="flex items-center space-x-4">
                                <button
                                    type="button"
                                    onClick={() => setIsArtistFirst(true)}
                                    className={`px-4 py-2 rounded transition-colors ${isArtistFirst
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                        }`}
                                    disabled={processMutation.isPending}
                                >
                                    Artist - Track
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setIsArtistFirst(false)}
                                    className={`px-4 py-2 rounded transition-colors ${!isArtistFirst
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                        }`}
                                    disabled={processMutation.isPending}
                                >
                                    Track - Artist
                                </button>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                                Select the format of your tracklist entries
                            </p>
                        </div>

                        {/* Tracklist Input */}
                        <div className="flex-1 flex flex-col">
                            <label htmlFor="tracklist" className="block text-sm font-medium text-gray-700 mb-2">
                                Tracklist *
                            </label>
                            <textarea
                                id="tracklist"
                                value={tracklistString}
                                onChange={(e) => setTracklistString(e.target.value)}
                                placeholder={`Paste your tracklist here, one track per line:\n\n${isArtistFirst
                                    ? 'Artist Name - Track Title\nAnother Artist - Another Track'
                                    : 'Track Title - Artist Name\nAnother Track - Another Artist'
                                    }`}
                                className="w-full h-64 p-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm resize-none"
                                disabled={processMutation.isPending}
                                required
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                Enter one track per line. The format should match your selection above.
                            </p>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="flex justify-end items-center space-x-3 p-6 border-t bg-gray-50">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
                            disabled={processMutation.isPending}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={!tracklistString.trim() || processMutation.isPending}
                            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                        >
                            {processMutation.isPending ? (
                                <>
                                    <svg
                                        className="animate-spin h-5 w-5 text-white"
                                        xmlns="http://www.w3.org/2000/svg"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                    >
                                        <circle
                                            className="opacity-25"
                                            cx="12"
                                            cy="12"
                                            r="10"
                                            stroke="currentColor"
                                            strokeWidth="4"
                                        ></circle>
                                        <path
                                            className="opacity-75"
                                            fill="currentColor"
                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                        ></path>
                                    </svg>
                                    <span>Processing...</span>
                                </>
                            ) : (
                                <span>Process Tracklist</span>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default AddTracklistModal;
