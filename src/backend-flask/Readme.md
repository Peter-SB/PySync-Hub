# Backed Flask
This is the backend of the PySync Hub desktop app. It was built with flask for flasks quick development and ease of use. The backend is responsible for handling the requests from the desktop application and returning the appropriate response. The backend is also responsible for handling the database and the data that is stored in it.

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
This file plays a special role in Flask because the app factory, create_app. 

### Services

This directory contains the service classes for handling business logic. These include

**Playlist Manager Service** - Service class for managing playlists such as adding, syncing and deleteig playlists.  
**Track Manager Service** - Service class for managing tracks mainly `fetch_playlist_tracks`.  
**Platform Services** - Service classes for interacting with different platforms such as Spotify and Soundcloud. For Spotify the Spotipy Library is used. Currently, only the Soundcloud service simply fetches using frontend calls.   
**Download Services** - Service classes for downloading tracks from platforms. This uses the yt-dlp library to download tracks from youtube (for spotify) or soundcloud. A base download service acts as a parent class for the platform download service classes to inherit from.  
**Export Services** - Service classes for exporting playlists to different formats. Currently, only the iTunes XML formats are supported.
