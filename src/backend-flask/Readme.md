# Backed Flask Technical Readme
PySync Hub is built on a layered architecture that follows clean code principles It was built with flask for Flasks quick development, ease of use, and for Pythons extensive libraries (specifically yt-dl). The backend is responsible for handling the requests from the desktop application, handling the database, and handling the download queue thread.

# Project Structure

## Top Level Project Structure
This is a standard flask project structure with the addition of a spec file used by pyinstaller to build the backend into an executable.
```
    backend-flask/
    ├─ app/                         - Main flask application logic
    ├─ tests/                       - Pytest Folder Tests 
    ├─ config.py                    - Configuration file for the flask application
    ├─ pysync-hub-backend.spec      - Pyinstaller spec file which is used to build the backend into an executable
    ├─ requirements.txt             - List of python packages required to run the backend
    └─ run.py                       - Entry point for the flask application               

```

## App Directory
This is the directory where the main flask application logic is stored. The app directory is broken down into the following subdirectories:
```
    app/
    ├─ repositories/                - Repository Pattern classes for interacting with the database.
    ├─ routes/                      - Route classes for handling requests
    ├─ services/                    - Service Pattern classes for handling business logic
    ├─ utils/                       - Utility classes for common functionality
    ├─ workers/                     - Download manager classes for handling background download worker
    ├─ __init__.py                  - Creates the flask application
    ├─ extensions.py                - Flask services for global access
    └─ models.py                    - SQLAlchemy Database models
```    

### \_\_init__.py In Flask
This file plays a special role in Flask because it contains the Flask app factory, create_app. 

### Services

This directory contains the service classes for handling business logic. These include

**Playlist Manager Service** - Service class for managing playlists such as adding, syncing and deleteig playlists.  
**Track Manager Service** - Service class for managing tracks mainly `fetch_playlist_tracks`.  
**Platform Services** - Service classes for interacting with different platforms such as Spotify and Soundcloud. For Spotify the Spotipy Library is used. Currently, only the Soundcloud service simply fetches using frontend calls.   
**Download Services** - Service classes for downloading tracks from platforms. This uses the yt-dlp library to download tracks from youtube (for spotify) or soundcloud. A base download service acts as a parent class for the platform download service classes to inherit from.  
**Export Services** - Service classes for exporting playlists to different formats. Currently, only the iTunes XML formats are supported.

# Key Design Patterns

- **Factory Pattern**: For creating platform-specific service instances
- **Repository Pattern**: For database abstraction
- **Service Pattern**: For business logic encapsulation
- **Observer Pattern**: For download status updates via WebSockets

This architecture was always front of mind in designing the program for clean separation of concerns, testability, and maintainability while also providing a stable platform for syncing and managing my music.