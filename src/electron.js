const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("path");
const fs = require("fs");
const yaml = require("js-yaml");
const { spawn, exec } = require("child_process");
const { dialog } = require("electron");



let mainWindow;
let flaskProcess = null;
const basePath =   path.join(__dirname, "../../../../");

function loadSettings() {
  try {
    // todo: check if dev or production mode
    const settings = yaml.load(fs.readFileSync(path.join(basePath, "settings.yml"), "utf8"));
    return {
      width: settings.WINDOW_WIDTH || 1920 * 0.75,
      height: settings.WINDOW_HEIGHT || 1080 * 0.75,
      zoomFactor: settings.WINDOW_ZOOM || 1,
      fullscreen: settings.FULLSCREEN || false,

    };
  } catch (error) {
    console.error("Error loading settings.yml:", error);
    return { width: 1920 * 0.75, height: 1080 * 0.75, zoomFactor: 1.0, fullscreen: false };
  }
}

const settings = loadSettings();
let zoomFactor = settings.zoomFactor;

function startFlask() {
  const flaskExePath = path.join(basePath, "dist/pysync-hub-backend", "pysync-hub-backend.exe");

  console.log("Starting Flask backend. Location:", flaskExePath);
  flaskProcess = spawn(flaskExePath, [], {
    detached: false, // false: Keep process tied to Electron
    stdio: "ignore",
    // shell: true
  });

  flaskProcess.on("error", (err) => {
    console.error("Failed to start Flask:", err);
  });

  flaskProcess.on("exit", (code) => {
    console.log(`Flask exited with code ${code}`);
  });
}

function stopFlask() {
  if (flaskProcess) {
    console.log("Stopping Flask backend...");
    flaskProcess.kill();
    flaskProcess = null;
  }
}

function startFlask_multiplatform() {
  const isWindows = process.platform === "win32";
  const isMac = process.platform === "darwin";

  let flaskCommand;
  let flaskArgs = [];
  let flaskOptions = { detached: false, stdio: "ignore" };

  if (isWindows) {
    flaskCommand = path.join(__dirname, "backend", "flask_app.exe"); // Windows .exe
  } else if (isMac || isLinux) {
    flaskCommand = path.join(__dirname, "backend", "flask_app"); // macOS executable
    flaskOptions.shell = true;
  } else {
    console.error("Unsupported OS detected.");
    return;
  }

  console.log(`Starting Flask backend: ${flaskCommand}`);
  flaskProcess = spawn(flaskCommand, flaskArgs, flaskOptions);

  flaskProcess.on("error", (err) => {
    console.error("Failed to start Flask:", err);
  });

  flaskProcess.on("exit", (code) => {
    console.log(`Flask exited with code ${code}`);
  });
}


function createWindow() {
  
  mainWindow = new BrowserWindow({
    width: settings.width,
    height: settings.height,
    resizable: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: true,
      enableRemoteModule: false,
      //preload: path.join(__dirname, "preload.js"),
    },
  });

  const startURL = false
    ? "http://localhost:3000"
    : `file://${path.join(__dirname, "frontend-react/build/index.html")}`;

  if (settings.fullscreen) {
    mainWindow.maximize();
  }
  mainWindow.loadURL(startURL);
  mainWindow.webContents.setZoomFactor(zoomFactor);

  mainWindow.on("closed", () => {
    mainWindow = null;
    stopFlask();
  });

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
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

app.on("ready", () => {
  startFlask();
  createWindow();
});

function displayDevDialog() {
  // _dirname: E:\Code\Python\PySync-Hub\dist\PySync-Hub-win32-x64\resources\app.asar, 
  // isPackaged: true, 
  // rpath: E:\Code\Python\PySync-Hub\dist\PySync-Hub-win32-x64\resources
  dialog.showMessageBox({
    type: "info",
    title: "Base Path",
    message: `__dirname: ${__dirname}, base_path: ${path.join(__dirname, "../../../../")}, isPackaged: ${app.isPackaged}, rpath: ${process.resourcesPath}`,
  });
}

app.on("window-all-closed", () => {
  stopFlask();

  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// "Emitted when all windows have been closed and the application will quit." 
app.on("will-quit", stopFlask);