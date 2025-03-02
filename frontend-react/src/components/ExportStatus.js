import React, { useEffect } from 'react';

function ExportStatus({ message }) {
  useEffect(() => {
    const timer = setTimeout(() => {
    }, 3000);
    return () => clearTimeout(timer);
  }, [message]);

  return (
    <div id="export-status" className="fixed bottom-5 left-1/2 transform -translate-x-1/2 z-50 bg-green-500 text-white text-center py-3 px-6 rounded max-w-4xl w-full md:w-3/4 lg:w-1/2 shadow-lg">
      {message}
    </div>
  );
}

export default ExportStatus;
