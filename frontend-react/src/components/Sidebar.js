import { FaMusic, FaCog, FaList } from "react-icons/fa";

export default function Sidebar({ onExport }) {
  return (
    <aside className="w-64 bg-gray-50 h-screen p-5 shadow-lg flex flex-col justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-gray-800 mb-7 text-3xl font-bold">PySync DJ Hub</h1>
        <nav>
          <ul>
            <li className="mb-4">
              <a href="/" className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700">
                <FaList className="text-xl" />
                <span>Playlists</span>
              </a>
            </li>
            <li className="mb-4">
              <a href="/tracks" className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700">
                <FaMusic className="text-xl" />
                <span>Tracks</span>
              </a>
            </li>
          </ul>
        </nav>
      </div>
      <div>
        <nav>
          <ul>
            <li>
              <a href="/settings" className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700">
                <FaCog className="text-xl" />
                <span>Settings</span>
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </aside>
  );
}