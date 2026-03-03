import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaDownload } from 'react-icons/fa';
import { useTracklists, useDeleteTracklist, useDownloadTracklist, useToggleTracklist } from '../hooks/useTracklists';
import AddTracklistModal from '../components/AddTracklistModal';

const SORT_DEFAULT_DIRECTION = {
    added: 'desc',
    title: 'asc',
    confirmed: 'desc',
};

function TracklistsPage() {
    const navigate = useNavigate();
    const { data: tracklists = [], isLoading, error, refetch } = useTracklists();
    const downloadMutation = useDownloadTracklist();
    const toggleMutation = useToggleTracklist();
    const [showAddModal, setShowAddModal] = useState(false);
    const [downloadingTracklistIds, setDownloadingTracklistIds] = useState([]);
    const [togglingTracklistIds, setTogglingTracklistIds] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [sortBy, setSortBy] = useState('added');
    const [sortDirection, setSortDirection] = useState(SORT_DEFAULT_DIRECTION.added);

    const handleTracklistClick = (tracklistId) => {
        navigate(`/tracklist/${tracklistId}`);
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

    const handleToggleDisabled = async (e, tracklistId, newState) => {
        e.stopPropagation();
        if (togglingTracklistIds.includes(tracklistId)) return;

        setTogglingTracklistIds((prev) => [...prev, tracklistId]);
        try {
            await toggleMutation.mutateAsync({ tracklistId, disabled: newState });
        } catch (error) {
            console.error('Error updating tracklist disabled state:', error);
        } finally {
            setTogglingTracklistIds((prev) => prev.filter((id) => id !== tracklistId));
        }
    };

    const getConfirmedEntriesCount = (tracklist) => {
        const entries = tracklist.tracklist_entries || tracklist.entries || [];
        return entries.filter((entry) => entry.confirmed_track_id).length;
    };

    const getAddedSortValue = (tracklist) => {
        if (tracklist.created_at) {
            const createdTs = new Date(tracklist.created_at).getTime();
            if (!Number.isNaN(createdTs)) {
                return createdTs;
            }
        }
        return Number(tracklist.id || 0);
    };

    const handleSortChange = (nextSortBy) => {
        if (sortBy === nextSortBy) return;
        setSortBy(nextSortBy);
        setSortDirection(SORT_DEFAULT_DIRECTION[nextSortBy]);
    };

    const handleSortDirectionToggle = () => {
        setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    };

    const sortedTracklists = useMemo(() => {
        const normalizedSearch = searchTerm.trim().toLowerCase();
        const filtered = normalizedSearch
            ? tracklists.filter((tracklist) => {
                const title = (tracklist.set_name || tracklist.name || '').toLowerCase();
                return title.includes(normalizedSearch);
            })
            : tracklists;

        const directionMultiplier = sortDirection === 'asc' ? 1 : -1;
        return filtered.slice().sort((a, b) => {
            if (sortBy === 'title') {
                const titleA = (a.set_name || a.name || '').toLowerCase();
                const titleB = (b.set_name || b.name || '').toLowerCase();
                const titleSort = titleA.localeCompare(titleB) * directionMultiplier;
                if (titleSort !== 0) return titleSort;
                return (Number(a.id || 0) - Number(b.id || 0)) * -1;
            }

            if (sortBy === 'confirmed') {
                const confirmedSort = (getConfirmedEntriesCount(a) - getConfirmedEntriesCount(b)) * directionMultiplier;
                if (confirmedSort !== 0) return confirmedSort;
                return (getAddedSortValue(a) - getAddedSortValue(b)) * -1;
            }

            const addedSort = (getAddedSortValue(a) - getAddedSortValue(b)) * directionMultiplier;
            if (addedSort !== 0) return addedSort;
            return (Number(a.id || 0) - Number(b.id || 0)) * -1;
        });
    }, [searchTerm, sortBy, sortDirection, tracklists]);

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
            <div className="bg-white p-5 rounded-lg shadow flex flex-col flex-1 min-h-0">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                    <h1 className="text-3xl font-semibold text-gray-800">Set Tracklists</h1>
                    <div className="flex flex-wrap items-center justify-end gap-3 w-full lg:w-auto">
                        <div className="flex items-center bg-white border border-gray-300 rounded-lg px-3 w-full sm:w-auto" style={{ height: '44px' }}>
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.35-4.35" />
                            </svg>
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Search tracklists by title"
                                className="w-full sm:w-64 p-2 text-gray-800 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none border-none"
                                style={{ height: '40px' }}
                            />
                        </div>
                        <div className="flex items-center gap-3 whitespace-nowrap">
                            <div className="flex items-center gap-1 p-1 pr-1.5 border border-gray-300 bg-gray-50 rounded-lg shadow-sm">
                                <span className="px-2 text-[11px] font-semibold uppercase tracking-wide text-gray-500">
                                    Sort
                                </span>
                                {[
                                    { key: 'added', label: 'Added' },
                                    { key: 'title', label: 'Title' },
                                    { key: 'confirmed', label: 'Count' },
                                ].map((option) => {
                                    const isActive = sortBy === option.key;
                                    return (
                                        <button
                                            key={option.key}
                                            onClick={() => handleSortChange(option.key)}
                                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${isActive
                                                ? 'bg-white text-gray-900 shadow-sm'
                                                : 'text-gray-600 hover:text-gray-800 hover:bg-white/80'
                                                }`}
                                            title={`Sort by ${option.label.toLowerCase()}`}
                                        >
                                            {option.label}
                                        </button>
                                    );
                                })}
                                <button
                                    onClick={handleSortDirectionToggle}
                                    className="ml-1 p-1.5 rounded-md text-gray-600 hover:text-gray-800 hover:bg-white/80 transition-colors"
                                    title={`Sort ${sortDirection === 'asc' ? 'ascending' : 'descending'}`}
                                    aria-label={`Sort ${sortDirection === 'asc' ? 'ascending' : 'descending'}`}
                                >
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        className={`h-4 w-4 transition-transform ${sortDirection === 'asc' ? 'rotate-180' : ''}`}
                                    >
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M7 10l5 5 5-5" />
                                    </svg>
                                </button>
                            </div>
                            <button
                                onClick={() => setShowAddModal(true)}
                                className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                                style={{ height: '48px' }}
                            >
                                Add Tracklist
                            </button>
                        </div>
                    </div>
                </div>

                {tracklists.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        <p className="text-lg mb-2">No tracklists yet</p>
                        <p className="text-sm">Click "Add Tracklist" to create your first one</p>
                    </div>
                ) : sortedTracklists.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        <p className="text-lg mb-2">No tracklists match that title</p>
                        <p className="text-sm">Try a different search</p>
                    </div>
                ) : (
                    <div className="flex-1 min-h-0 overflow-y-auto pr-1">
                        <div className="space-y-2">
                            {sortedTracklists.map((tracklist) => {
                                const confirmedEntriesCount = getConfirmedEntriesCount(tracklist);
                                const downloadableTracks = getDownloadableTracks(tracklist);
                                const downloadCount = downloadableTracks.length;
                                const isDownloading = downloadingTracklistIds.includes(tracklist.id);
                                const isToggling = togglingTracklistIds.includes(tracklist.id);

                                return (
                                    <div
                                        key={tracklist.id}
                                        onClick={() => handleTracklistClick(tracklist.id)}
                                        className={`flex items-center justify-between p-3 border border-gray-300 rounded-lg cursor-pointer transition-colors ${tracklist.disabled ? 'bg-gray-200 hover:bg-gray-200' : 'hover:bg-gray-50'}`}
                                    >
                                        <div className={`flex-1 min-w-0 ${tracklist.disabled ? 'text-gray-500' : 'text-gray-600'}`}>
                                            <div className="flex items-center flex-wrap gap-x-3 gap-y-1">
                                                <h3 className={`text-lg font-semibold truncate ${tracklist.disabled ? 'text-gray-600' : 'text-gray-800'}`}>
                                                    {tracklist.set_name || `Tracklist ${tracklist.id}`}
                                                </h3>
                                                <span className="text-sm">
                                                    {confirmedEntriesCount} Confirmed Tracks
                                                </span>
                                                {tracklist.created_at && (
                                                    <span className="text-sm">
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
                                            <label
                                                htmlFor={`toggle-tracklist-${tracklist.id}`}
                                                className="relative inline-flex items-center cursor-pointer ml-2"
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                <input
                                                    type="checkbox"
                                                    id={`toggle-tracklist-${tracklist.id}`}
                                                    onChange={(e) => handleToggleDisabled(e, tracklist.id, !tracklist.disabled)}
                                                    checked={tracklist.disabled}
                                                    disabled={isToggling}
                                                    className="sr-only peer"
                                                />
                                                <div className="relative w-[35px] h-[21px] bg-gray-400 border border-gray-300 rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:ring-gray-600 disabled:opacity-50 disabled:pointer-events-none
                                                    peer-checked:bg-gray-100
                                                    before:inline-block before:w-4 before:h-4 before:bg-white before:rounded-full before:shadow before:transition-all before:ease-in-out before:duration-200
                                                    before:translate-x-[17px] before:translate-y-[-0.5px] peer-checked:before:translate-x-0">
                                                </div>
                                            </label>
                                            {/* <button
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
                                        </button> */}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>

            {showAddModal && (
                <AddTracklistModal
                    existingTracklists={tracklists}
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
