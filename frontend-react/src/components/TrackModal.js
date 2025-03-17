// src/components/TrackModal.js
import React, { useState } from 'react';
import { backendUrl } from '../config';

const TrackModal = ({ track, onClose, onUpdate }) => {
    const [downloadUrl, setDownloadUrl] = useState(track.download_url || '');
    const [downloadLocation, setDownloadLocation] = useState(track.download_location || '');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [downloading, setDownloading] = useState(false);

    const handleSave = async () => {
        setSaving(true);
        setError('');
        try {
            const response = await fetch(`${backendUrl}/api/tracks/${track.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    download_url: downloadUrl,
                    download_location: downloadLocation,
                }),
            });
            if (response.ok) {
                const updatedTrack = await response.json();
                onUpdate(updatedTrack);
                onClose();
            } else {
                const data = await response.json();
                setError(data.error || 'Failed to update track');
            }
        } catch (err) {
            console.error(err);
            setError('Error updating track');
        } finally {
            setSaving(false);
        }
    };

    const handleReDownload = async () => {
        setSaving(true);
        setError('');
        try {
            const saveResponse = await fetch(`${backendUrl}/api/tracks/${track.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    download_url: downloadUrl,
                }),
            });

            if (!saveResponse.ok) {
                const saveErrorData = await saveResponse.json();
                setError(saveErrorData.error || 'Failed to save download URL');
                return; // Cancel re-download if save fails
            }
        } catch (err) {
            console.error(err);
            setError('Error saving download URL');
            return; // Cancel re-download if save fails
        } finally {
            setSaving(false);
        }
        setDownloading(true);
        setError('');
        try {
            const response = await fetch(`${backendUrl}/api/tracks/${track.id}/download`, {
                method: 'POST',
            });

            if (response.ok) {
                const updatedTrack = await response.json();
                onUpdate(updatedTrack);
            } else {
                const data = await response.json();
                setError(data.error || 'Failed to re-download track');
            }
        } catch (err) {
            console.error(err);
            setError('Error re-downloading track');
        } finally {
            setDownloading(false);
        }

    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
            <div
                className="bg-white rounded-lg shadow-lg p-6 w-1/2 relative"
                onClick={(e) => e.stopPropagation()}
            >
                {/* <button
                    onClick={onClose}
                    className="absolute top-0 right-1 text-gray-600 hover:text-gray-800 text-2xl"
                >
                    &times;
                </button> */}
                <div className='flex'>
                    <div className="flex-1">

                        {/* <h2 className="text-xl font-semibold mb-4">Edit Track Details</h2> */}
                        <div className="mb-4">
                            <label className="block text-gray-700">Name</label>
                            <p className="text-black tex text-lg font-medium">{track.name}</p>
                        </div>
                        <div className="mb-4">
                            <label className="block text-gray-600">Artist</label>
                            <p className="text-gray-900 tex text-lg">{track.artist}</p>
                        </div>
                        {track.album && (
                            <div className="mb-4">
                                <label className="block text-gray-600">Album</label>
                                <p className="text-gray-900 tex text-lg">{track.album}</p>
                            </div>
                        )}
                    </div>
                    {track.album_art_url && (
                        <div className="ml-4">
                            <img
                                src={track.album_art_url}
                                alt={`${track.album || 'Album'} cover`}
                                className="w-36 h-36 object-cover rounded"
                            />
                        </div>
                    )}
                </div>

                <div className="mb-4 flex items-center space-x-2">
                    <div className="flex-1">
                        <label className="block text-gray-700 font-medium">Download URL</label>
                        <input
                            type="text"
                            value={downloadUrl}
                            onChange={(e) => setDownloadUrl(e.target.value)}
                            className="mt-1 p-2 border rounded w-full"
                            placeholder="Enter download URL"
                        />
                    </div>
                    <div className="flex justify-center mt-6">
                        <button
                            onClick={handleReDownload}
                            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                            disabled={downloading}
                        >
                            {downloading ? 'Downloading...' : 'ReDownload'}
                        </button>
                    </div>
                </div>

                <div className="mb-4">
                    <label className="block text-gray-700 font-medium">Relative Download Location</label>
                    <input
                        type="text"
                        value={downloadLocation}
                        onChange={(e) => setDownloadLocation(e.target.value)}
                        className="mt-1 p-2 border rounded w-full"
                        placeholder="Enter download location"
                    />
                </div>

                {track.notes_errors && (
                        <div className="mb-4">
                        <p className="text-red-500 tex text-lg">{track.notes_errors}</p>
                    </div>
                    )}

                {error && (
                    <div className="mb-4 text-red-600">
                        {error}
                    </div>
                )}
                <div className="flex justify-end space-x-2">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
                        disabled={saving}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        disabled={saving}
                    >
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default TrackModal;
