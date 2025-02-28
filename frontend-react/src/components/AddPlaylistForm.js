import React, { useState } from 'react';

function AddPlaylistForm({ onPlaylistAdded, setError }) {
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!playlistUrl.trim()) return;
    setIsSubmitting(true);
    setError('');
    try {
      const response = await fetch('http://localhost:5000/api/playlists', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url_or_id: playlistUrl }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.error || 'Failed to add playlist');
      } else {
        onPlaylistAdded();
        setPlaylistUrl('');
      }
    } catch (error) {
      console.error(error);
      setError('Failed to add playlist');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-10 mb-10 ml-5 mr-11 mt-6">
      <div className="flex gap-4 ">
        <input 
          type="text"
          value={playlistUrl}
          onChange={(e) => setPlaylistUrl(e.target.value)}
          placeholder="Enter Spotify playlist URL or ID"
          className="flex-1 p-2 border rounded"
        />
        <button 
          type="submit"
          disabled={!playlistUrl.trim() || isSubmitting}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:cursor-not-allowed"
          style={{ marginRight: '47px' }}
        >
          {isSubmitting ? 'Adding...' : 'Add Playlist'}
        </button>
      </div>
    </form>
  );
}

export default AddPlaylistForm;
