import React, { useState, useEffect } from 'react';
import { FaMusic, FaCog, FaList, FaGithub, FaExclamationTriangle, FaClipboardList, FaSyncAlt } from "react-icons/fa";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faQuestion } from "@fortawesome/free-solid-svg-icons";
import { Link } from 'react-router-dom';
import { version } from '../config';
import ExportButton from './ExportButton';
import ExportStatus from './ExportStatus';

export default function Sidebar() {
  const [versionStatus, setVersionStatus] = useState(null);
  const [exportMessage, setExportMessage] = useState('');

  useEffect(() => {
    const checkVersion = async () => {
      try {
        const response = await fetch('https://api.github.com/repos/Peter-SB/PySync-Hub/releases/latest');
        const data = await response.json();
        const latestVersion = data.tag_name.replace('v', '');

        const [currentMajor, currentMinor] = version.split('.').map(Number);
        const [latestMajor, latestMinor] = latestVersion.split('.').map(Number);

        if (currentMajor < latestMajor) {
          setVersionStatus('major');
        } else if (currentMinor < latestMinor) {
          setVersionStatus('minor');
        }
      } catch (error) {
        console.error('Error checking version:', error);
      }
    };

    checkVersion();
  }, []);

  const getVersionIcon = () => {
    let updateIcon = null;
    let updateText = null;

    if (versionStatus === 'major') {
      updateIcon = <FaExclamationTriangle className="text-xl text-red-500 mt-1" />;
      updateText = 'Major Update Available';
    } else if (versionStatus === 'minor') {
      updateIcon = <FaExclamationTriangle className="text-xl text-green-500 mt-1" />;
      updateText = 'Minor Update Available';
    }

    const baseContent = (
      <>
        <FaGithub className="text-xl mt-0.5" />
        <span className="mx-3">Version: v{version}</span>
        {updateIcon}
      </>
    );

    // If there's an update text, show it below the version info
    if (updateText) {
      return (
        <div className="flex-col items-center justify-end h-full">
          <span className="flex flex-row" title="Urgent update available">
            {baseContent}
          </span>
          <span className="text-xs text-gray-400">{updateText}</span>
        </div>
      );
    }

    // Otherwise, just show the base content
    return (
      <span className="flex flex-row" title="Urgent update available">
        {baseContent}
      </span>
    );
  };

  return (
    <aside className="w-64 bg-white h-screen p-5 shadow-lg flex flex-col justify-between relative border bw-3 z-50 fixed">
      <div>
        <div className="flex justify-center mb-5 mr-2">
          <img
            src={"/images/new-logo.png"}
            alt="Sidebar Logo"
            className="h-32 w-auto"
          />
        </div>
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
              <Link to="/tracklists" className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700 hover:text-white">
                <FaClipboardList className="text-xl" />
                <span>Tracklists</span>
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
              <Link to="/settings" className="flex items-center space-x-3 p-3 mt-1 rounded hover:bg-gray-700 hover:text-white">
                <FaCog className="text-xl" />
                <span>Settings</span>
              </Link>
            </li>
          </ul>
        </nav>
        <div className="">
          <a
            href="https://github.com/Peter-SB/PySync-Hub/releases"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-3 p-3 rounded hover:bg-gray-700 hover:text-white"
          >
            {getVersionIcon()}
          </a>
        </div>
        <div className="border-t border-gray-200 my-2" />
        <nav>
          <ul>
            <li>
              <div className="mt-1 pt-3 flex justify-center">
                <ExportButton setExportMessage={setExportMessage} />
              </div>
            </li>
          </ul>
        </nav>
        {exportMessage && <ExportStatus message={exportMessage} />}
      </div>
    </aside>
  );
}
