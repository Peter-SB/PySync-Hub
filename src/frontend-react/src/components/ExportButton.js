import React, { useState, useEffect } from 'react';
import { useExportAll } from '../hooks/usePlaylistMutations';

const LoadingSpinnerIcon = () => (
    <svg className="animate-spin h-6 w-6 text-white ml-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
);

const TickSuccessIcon = () => (
    <svg className="h-6 w-6 text-white ml-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
    </svg>
);

const RekordboxIconImg = () => <img src="/icons/rekordbox.svg" alt="Rekordbox" className="h-6 w-6 rounded-lg m-0.5" />;
const ExportIconImg = () => <img src="/icons/export.svg" alt="Export" className="h-6 w-6 rounded-lg" />;

function ExportButton({ setExportMessage }) {
    const [isCompleted, setIsCompleted] = useState(false);
    const exportMutation = useExportAll();

    // Reset the completed state when the mutation state changes
    useEffect(() => {
        if (exportMutation.isError) {
            setIsCompleted(false);
        } else if (exportMutation.isSuccess) {
            setIsCompleted(true);
            // Reset after some time
            const timer = setTimeout(() => {
                setIsCompleted(false);
                setExportMessage("");
            }, 5000);
            return () => clearTimeout(timer);
        }
    }, [exportMutation.isError, exportMutation.isSuccess]);

    // Update export message based on mutation state
    useEffect(() => {
        if (exportMutation.isSuccess && exportMutation.data) {
            setExportMessage("Export successful: " + exportMutation.data.export_path);
        } else if (exportMutation.isError && exportMutation.error) {
            const errorMessage = exportMutation.error.response?.data?.error ||
                exportMutation.error.message ||
                "Unknown export error";
            setExportMessage("Export failed: " + errorMessage);
        }
    }, [exportMutation.isSuccess, exportMutation.isError, exportMutation.data, exportMutation.error, setExportMessage]);

    const handleExportClick = () => {
        if (exportMutation.isPending) return;
        exportMutation.mutate();
    };

    return (
        <button
            onClick={handleExportClick}
            className="flex items-center px-3 py-2 bg-gray-900 hover:bg-black text-white rounded-lg shadow-md"
            disabled={exportMutation.isPending || (isCompleted && !exportMutation.isPending)}
        >
            <span className="font-medium text-l">
                {exportMutation.isPending ? 'Exporting...' : isCompleted ? 'Exported!' : 'Export All'}
            </span>
            {exportMutation.isPending ? (
                <LoadingSpinnerIcon />
            ) : isCompleted ? (
                <TickSuccessIcon />
            ) : (
                <div className="bg-white p-0.25 flex items-center justify-center rounded-lg ml-2">
                    <RekordboxIconImg />
                    <ExportIconImg />
                </div>
            )}
        </button>
    );
}

export default ExportButton;
