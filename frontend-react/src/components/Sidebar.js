import { FaMusic, FaCog, FaList } from "react-icons/fa";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faQuestion } from "@fortawesome/free-solid-svg-icons";


export default function Sidebar({ onExport }) {
  return (
    <aside className="w-64 bg-white h-screen p-5 shadow-lg flex flex-col justify-between relative border bw-3 z-50 fixed">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 mb-7 text-3xl font-bold">PySync DJ Hub</h1>
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
            <li className="mb-4">
              <a href="/help" className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700">
                <FontAwesomeIcon icon={faQuestion} className="text-2xl mx-1" />
                <span>Help</span>
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