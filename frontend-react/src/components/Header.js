import React from 'react';

function Header({ onExport }) {
  return (
    <div className="flex items-center justify-between pb-5">
      <h1 className="text-4xl font-bold text-gray-900">PySync DJ Hub</h1>
      <button 
        onClick={onExport}
        className="flex items-center px-4 py-2 bg-gray-700 hover:bg-black text-white rounded-lg shadow-md"
      >
        <span className="font-medium text-l">Export</span>
        <div className="bg-white p-0.25 flex items-center justify-between rounded-lg ml-2">
          <img src="/static/icons/rekordbox.svg" alt="Rekordbox" className="h-6 w-6 rounded-lg m-0.5" />
          <img src="/static/icons/export.svg" alt="Export" className="h-6 w-6 rounded-lg" />
        </div>
      </button>
    </div>
  );
}

export default Header;
