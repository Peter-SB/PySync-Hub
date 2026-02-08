// src/components/AddPlaylistForm.js
import React, { useState, useRef, useEffect } from 'react';
import { useAddPlaylist } from '../hooks/usePlaylistMutations';

function AddPlaylistForm({ className = '' }) {
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [trackLimit, setTrackLimit] = useState('');
  const [dateLimit, setDateLimit] = useState('');
  const [showOptions, setShowOptions] = useState(false);

  const addPlaylistMutation = useAddPlaylist();

  // Create a ref for the form container
  const containerRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setShowOptions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!playlistUrl.trim()) return;

    const payload = {
      url_or_id: playlistUrl,
      track_limit: trackLimit || undefined,
      date_limit: dateLimit || undefined,
    };

    setShowOptions(false);

    addPlaylistMutation.mutate(payload, {
      onSuccess: () => {
        setPlaylistUrl('');
        setTrackLimit('');
        setDateLimit('');
      }
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`${className}`}
      ref={containerRef}
    >
      <div className="relative">
        <div className="flex w-full">
          <input
            type="text"
            value={playlistUrl}
            onChange={(e) => setPlaylistUrl(e.target.value)}
            placeholder="Enter Playlist URL"
            className="flex-1 p-3 border rounded focus:outline-none focus:ring focus:border-blue-300 transition-colors"
          />
          <div className="relative flex">
            <button
              type="submit"
              disabled={!playlistUrl.trim() || addPlaylistMutation.isPending}
              className="px-4 py-3 bg-blue-600 text-white rounded-l hover:bg-blue-700 disabled:cursor-not-allowed transition-colors "
            >
              {addPlaylistMutation.isPending ? 'Adding...' : 'Add Playlist'}
            </button>
            <button
              type="button"
              className=" bg-blue-600 text-white rounded-r hover:bg-blue-700 transition-colors w-9 items-center flex justify-center"
              onClick={() => setShowOptions((prev) => !prev)}
            >
              <svg
                className={`w-5 h-5 transform transition-transform ${!showOptions ? 'rotate-180' : 'rotate-0'}`}
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 15l7-7 7 7"
                />
              </svg>
            </button>
          </div>
        </div>
        {showOptions && (
          <div className="absolute left-0 right-0 mt-2 p-4 bg-white border rounded shadow-lg z-10 transition-all text-gray-600">
            <div className="flex items-center space-x-4">
              <label htmlFor="trackLimit" className="text-sm">Track Limit</label>
              <input
                type="number"
                id="trackLimit"
                placeholder="None"
                value={trackLimit}
                onChange={(e) => setTrackLimit(e.target.value)}
                className="mt-1 p-2 border rounded focus:outline-none focus:ring focus:border-blue-300 transition-colors w-24 h-8"
              />
              {!playlistUrl.includes("soundcloud") && (
                <div>
                  <label htmlFor="dateLimit" className="text-sm">Date Limit</label>
                  <input
                    type="date"
                    id="dateLimit"
                    value={dateLimit}
                    onChange={(e) => setDateLimit(e.target.value)}
                    className="mt-1 p-2 border rounded focus:outline-none focus:ring focus:border-blue-300 transition-colors w-40 h-8"
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </form>
  );
}

export default AddPlaylistForm;
