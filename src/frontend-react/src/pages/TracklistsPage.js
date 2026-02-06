import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaDownload } from 'react-icons/fa';
import { useTracklists, useDeleteTracklist, useDownloadTracklist } from '../hooks/useTracklists';
import AddTracklistModal from '../components/AddTracklistModal';

function TracklistsPage() {
    const navigate = useNavigate();
    const { data: tracklists = [], isLoading, error, refetch } = useTracklists();
    const deleteMutation = useDeleteTracklist();
    const downloadMutation = useDownloadTracklist();
    const [showAddModal, setShowAddModal] = useState(false);
    const [downloadingTracklistIds, setDownloadingTracklistIds] = useState([]);

    const handleTracklistClick = (tracklistId) => {
        navigate(`/tracklist/${tracklistId}`);
    };

    const handleDelete = async (e, tracklistId) => {
        e.stopPropagation();
        if (!window.confirm('Are you sure you want to delete this tracklist?')) return;

        try {
            await deleteMutation.mutateAsync(tracklistId);
        } catch (error) {
            console.error('Error deleting tracklist:', error);
        }
    };

    const getDownloadableTracks = (tracklist) => {
        const entries = tracklist.tracklist_entries || tracklist.entries || [];
        const trackMap = new Map();
        entries.forEach((entry) => {
            const track = entry.confirmed_track;
            if (track && !track.download_location && !trackMap.has(track.id)) {
                trackMap.set(track.id, track);
            }
        });
        return Array.from(trackMap.values());
    };

    const handleDownloadTracklist = async (e, tracklist) => {
        e.stopPropagation();
        const tracksToDownload = getDownloadableTracks(tracklist);
        if (tracksToDownload.length === 0) return;
        if (downloadingTracklistIds.includes(tracklist.id)) return;

        setDownloadingTracklistIds((prev) => [...prev, tracklist.id]);

        try {
            const response = await downloadMutation.mutateAsync(tracklist.id);
            if (response?.failed?.length > 0) {
                alert(`Failed to download ${response.failed.length} track(s). Check console for details.`);
            }
        } catch (error) {
            console.error('Error downloading tracklist:', error);
            alert(`Failed to download tracklist: ${error.message}`);
        } finally {
            setDownloadingTracklistIds((prev) => prev.filter((id) => id !== tracklist.id));
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-xl text-gray-600">Loading tracklists...</div>
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

    return (
        <div className="flex flex-col h-screen p-4 pt-2">
            <div className="bg-white p-5 rounded-lg mb-4 shadow">
                <div className="flex justify-between items-center mb-4">
                    <h1 className="text-3xl font-semibold text-gray-800">Tracklists</h1>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                    >
                        Add Tracklist
                    </button>
                </div>

                {tracklists.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        <p className="text-lg mb-2">No tracklists yet</p>
                        <p className="text-sm">Click "Add Tracklist" to create your first one</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {tracklists.map((tracklist) => {
                            const downloadableTracks = getDownloadableTracks(tracklist);
                            const downloadCount = downloadableTracks.length;
                            const isDownloading = downloadingTracklistIds.includes(tracklist.id);

                            return (
                                <div
                                    key={tracklist.id}
                                    onClick={() => handleTracklistClick(tracklist.id)}
                                    className="flex items-center justify-between p-4 border border-gray-300 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                                >
                                    <div className="flex-1">
                                        <h3 className="text-lg font-semibold text-gray-800">
                                            {tracklist.set_name || `Tracklist ${tracklist.id}`}
                                        </h3>
                                        <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                                            <span>
                                                {tracklist.tracklist_entries?.length || 0} entries
                                                {/*todo: add downloaded count  */}
                                            </span>
                                            {tracklist.created_at && (
                                                <span>
                                                    Created: {new Date(tracklist.created_at).toLocaleDateString()}
                                                </span>
                                            )}
                                            {tracklist.folder_id && (
                                                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                                                    In Folder
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        {downloadCount > 0 && (
                                            <button
                                                onClick={(e) => handleDownloadTracklist(e, tracklist)}
                                                disabled={isDownloading}
                                                className="flex items-center gap-2 px-3 py-2 text-green-700 bg-green-50 rounded hover:bg-green-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                                title={`Download ${downloadCount} track${downloadCount !== 1 ? 's' : ''}`}
                                            >
                                                <FaDownload className="h-4 w-4" />
                                                <span className="text-xs font-medium">
                                                    {isDownloading ? 'Downloading...' : `Download (${downloadCount})`}
                                                </span>
                                            </button>
                                        )}
                                        <button
                                            onClick={(e) => handleDelete(e, tracklist.id)}
                                            disabled={deleteMutation.isPending}
                                            className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                                            title="Delete tracklist"
                                        >
                                            <svg
                                                xmlns="http://www.w3.org/2000/svg"
                                                className="h-5 w-5"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    strokeWidth={2}
                                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                                />
                                            </svg>
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {showAddModal && (
                <AddTracklistModal
                    onClose={() => setShowAddModal(false)}
                    onSuccess={(createdTracklist) => {
                        setShowAddModal(false);
                        if (createdTracklist?.id) {
                            navigate(`/tracklist/${createdTracklist.id}`);
                        } else {
                            refetch();
                        }
                    }}
                />
            )}
        </div>
    );
}

export default TracklistsPage;
