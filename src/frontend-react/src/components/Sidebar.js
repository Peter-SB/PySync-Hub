import { FaMusic, FaCog, FaList } from "react-icons/fa";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faQuestion } from "@fortawesome/free-solid-svg-icons";
import { Link } from 'react-router-dom';


export default function Sidebar({ onExport }) {
  return (
    <aside className="w-64 bg-white h-screen p-5 shadow-lg flex flex-col justify-between relative border bw-3 z-50 fixed">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 mb-7 text-3xl font-bold">PySync DJ Hub</h1>
        <nav>
          <ul>
            <li className="mb-4">
              <Link to="/" className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700 hover:text-white">
                <FaList className="text-xl" />
                <span>Playlists</span>
              </Link>
            </li>
            <li className="mb-4">
              <Link to="/tracks" className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700 hover:text-white">
                <FaMusic className="text-xl" />
                <span>Tracks</span>
              </Link>
            </li>
            <li className="mb-4">
              <a href="https://github.com/Peter-SB/PySync-Hub/blob/master/docs/Help.md" target="_blank" rel="noopener noreferrer" className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700 hover:text-white">
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
              <Link to="/settings" className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700 hover:text-white">
                <FaCog className="text-xl" />
                <span>Settings</span>
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </aside>
  );
}