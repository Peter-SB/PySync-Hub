const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let mainWindow;
let pythonProcess;

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      // For security: disable Node integration in the renderer
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  const startURL = isDev
    ? "http://localhost:3000"
    : `file://${path.join(__dirname, "frontend-react/build/index.html")}`;

  mainWindow.loadURL(startURL);

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.on('ready', createWindow);

app.on("window-all-closed", () => {
  // Terminate the Python process when all windows are closed
  // if (pythonProcess) {
  //   pythonProcess.kill();
  // }
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (mainWindow === null) {
    createWindow();
  }
});
