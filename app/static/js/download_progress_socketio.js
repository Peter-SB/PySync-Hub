// static/js/socketio.js

// Initialize the Socket.IO client
var socket = io();

// Listen for download_status events from the server
socket.on("download_status", function(data) {
    console.log("Received download status update:", data);

    var statusEl = document.getElementById("download-status-" + data.id);
    if (!statusEl) return;

    if (data.status === "queued") {
        statusEl.innerHTML = '<span class="text-yellow-500 font-bold">Queued</span>';
    } else if (data.status === "downloading") {
        statusEl.innerHTML = `
            <div class="flex items-center">
                <div class="w-32 bg-gray-300 rounded-full h-2 mr-2">
                    <div
                        class="bg-blue-500 h-2 rounded-full"
                        style="width: ${data.progress || 0}%;">
                    </div>
                </div>
                <button onclick="cancelDownload(${data.id})" class="px-2 py-1 bg-red-600 text-white rounded">
                    Cancel
                </button>
            </div>
        `;
    } else if (data.status === "ready") {
        statusEl.innerHTML = `
            <button
                    hx-post="/playlists/refresh"
                    hx-vals='{"playlist_ids": [${data.id}]}'
                    hx-target="#playlist-list"
                    class="px-3 py-1 text-sm bg-gray-100 rounded-lg hover:bg-gray-200">
                Sync
            </button>
        `;
    }
});

// Function to cancel a download
function cancelDownload(playlistId) {
    fetch('/download/' + playlistId + '/cancel', { method: 'DELETE' })
      .then(response => response.text())
      .then(html => {
          document.getElementById('playlist-list').innerHTML = html;
      });
}
