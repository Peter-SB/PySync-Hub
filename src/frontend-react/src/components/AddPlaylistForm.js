// src/components/AddPlaylistForm.js
import React, { useState, useRef, useEffect } from 'react';
import { backendUrl } from '../config';

function AddPlaylistForm({ onPlaylistAdded, setError }) {
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [trackLimit, setTrackLimit] = useState('');
  const [dateLimit, setDateLimit] = useState('');
  const [showOptions, setShowOptions] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

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
    setIsSubmitting(true);
    setError('');
    try {
      const payload = {
        url_or_id: playlistUrl,
        track_limit: trackLimit,
        date_limit: dateLimit,
      };

      setShowOptions(false);
      const response = await fetch(`${backendUrl}/api/playlists`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        setError(data.error || 'Failed to add playlist');
      } else {
        onPlaylistAdded();
        setPlaylistUrl('');
        setTrackLimit('');
        setDateLimit('');
      }
    } catch (error) {
      console.error(error);
      setError('Failed to add playlist');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 mb-5 mt-6"
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
            onFocus={() => setShowOptions(true)}
          />
          <button
            type="submit"
            disabled={!playlistUrl.trim() || isSubmitting}
            className="ml-2 px-4 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? 'Adding...' : 'Add Playlist'}
          </button>
        </div>
        {showOptions && (
          <div className="absolute left-0 right-0 mt-2 p-4 bg-white border rounded shadow-lg z-10 transition-all text-gray-600">
            <div className="flex items-center space-x-4">
              <div className="flex flex-col">
                <label htmlFor="trackLimit" className="text-sm">Track Limit</label>
                <input
                  type="number"
                  id="trackLimit"
                  placeholder="None"

                  value={trackLimit}
                  onChange={(e) => setTrackLimit(e.target.value)}
                  className="mt-1 p-2 border rounded focus:outline-none focus:ring focus:border-blue-300 transition-colors w-24 h-8"
                />
              </div>
              <div className="flex flex-col">
                <label htmlFor="dateLimit" className="text-sm">Date Limit</label>
                <input
                  type="date"
                  id="dateLimit"
                  value={dateLimit}
                  onChange={(e) => setDateLimit(e.target.value)}
                  className="mt-1 p-2 border rounded focus:outline-none focus:ring focus:border-blue-300 transition-colors w-40 h-8"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </form>
  );
}

export default AddPlaylistForm;
