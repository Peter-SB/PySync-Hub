const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");
const yaml = require("js-yaml");

let mainWindow;

// Load settings from settings.yml
function loadSettings() {
  try {
    const settings = yaml.load(fs.readFileSync(path.join(__dirname, "settings.yml"), "utf8"));
    return {
      width: settings.WINDOW_WIDTH || 1920*0.75,
      height: settings.WINDOW_HEIGHT || 1080*0.75,
      zoomFactor: settings.WINDOW_ZOOM || 1,
      fullscreen: settings.FULLSCREEN || false,

    };
  } catch (error) {
    console.error("Error loading settings.yml:", error);
    return { width: 1920*0.75, height: 1080*0.75, zoomFactor: 1.0, fullscreen: false };
  }
}

const settings = loadSettings();
let zoomFactor = settings.zoomFactor;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: settings.width,
    height: settings.height,
    resizable: true, 
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      //preload: path.join(__dirname, "preload.js"),
    },
  });

  const startURL = true
    ? "http://localhost:3000"
    : `file://${path.join(__dirname, "frontend-react/build/index.html")}`;

  if (settings.fullscreen) {
    mainWindow.maximize();
  }
  mainWindow.loadURL(startURL);
  mainWindow.webContents.setZoomFactor(zoomFactor);

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

ipcMain.on("zoom-in", () => {
  if (mainWindow) {
    zoomFactor += 0.1;
    mainWindow.webContents.setZoomFactor(zoomFactor);
  }
});

ipcMain.on("zoom-out", () => {
  if (mainWindow) {
    zoomFactor = Math.max(0.5, zoomFactor - 0.1);
    mainWindow.webContents.setZoomFactor(zoomFactor);
  }
});

ipcMain.on("reset-zoom", () => {
  if (mainWindow) {
    zoomFactor = settings.zoomFactor;
    mainWindow.webContents.setZoomFactor(zoomFactor);
  }
});

app.on("ready", createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (mainWindow === null) {
    createWindow();
  }
});
