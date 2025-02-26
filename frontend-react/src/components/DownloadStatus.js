import React from "react";

function DownloadStatus({ playlist, handleSyncClick, handleCancelClick }) {
    return (
        <div id={`download-status-${playlist.id}`} className="ml-4">
            {playlist.download_status === 'queued' && (
                <div className="flex items-center space-x-2">
                    <span className="text-yellow-500 font-bold">Queued</span>
                    <button onClick={handleCancelClick} className="px-2 py-1 bg-red-600 text-white rounded">
                        Cancel
                    </button>
                </div>
            )}
            {playlist.download_status === 'downloading' && (
                <div className="flex items-center space-x-2">
                    <div className="w-32 bg-gray-300 rounded-full h-2 mr-2">
                        <div
                            id={`progress-bar-${playlist.id}`}
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${playlist.download_progress}%` }}>
                        </div>
                    </div>
                    <button onClick={handleCancelClick} className="px-2 py-1 bg-red-600 text-white rounded">
                        Cancel
                    </button>
                </div>
            )}
            {playlist.download_status === 'ready' && (
                !playlist.disabled ? (
                    <button onClick={handleSyncClick} className="px-3 py-1 text-sm bg-gray-100 rounded-lg hover:bg-gray-200">
                        Sync
                    </button>
                ) : (
                    <button className="px-3 py-1 text-sm bg-gray-100 rounded-lg opacity-50" disabled>
                        Sync
                    </button>
                )
            )}
        </div>
    );
}

export default DownloadStatus;