import { FaMusic, FaCog } from "react-icons/fa";

export default function Sidebar({ onExport }) {
  return (
    <aside className="w-64 bg-gray-50 h-screen p-5 shadow-lg flex flex-col justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-gray-800 mb-7 text-3xl font-bold">PySync DJ Hub</h1>
        <nav>
          <ul>
            <li className="mb-4">
              <a href="/" className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700">
                <FaMusic className="text-xl" />
                <span>Playlists</span>
              </a>
            </li>
            <li>
              <a href="/settings" className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700">
                <FaCog className="text-xl" />
                <span>Settings</span>
              </a>
            </li>
          </ul>
        </nav>
        </div>
      <button 
        onClick={onExport}
        className="flex items-center justify-center px-2 py-2 bg-gray-600 hover:bg-black text-white rounded shadow-md mt-4 mx-1"
      >
        <span className="font-medium text-l">Export</span>
        <div className="bg-white p-0.25 flex items-center rounded ml-2 justify-between">
          <img src="/icons/rekordbox.svg" alt="Rekordbox" className="h-6 w-6 rounded m-0.5" />
          <img src="/icons/export.svg" alt="Export" className="h-6 w-6 rounded" />
        </div>
      </button>
    </aside>
  );
}