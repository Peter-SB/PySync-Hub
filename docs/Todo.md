# Todo List

## Export
- export page?
- error display
- Potential Bug: Playlists With Same Names - Tested, not an issue.

## Playlist/Track Managment
 - Better Errors
 - Improve ui updates
 - Repository Patter Use
 - Disable individual tracks
 - ✅ Downloaded count (home screen) is not displaying correctly when finished downloading


## Downloading
- Add Quick Sync (That will not check file locations, only download new tracks without a location, maybe also not check playlist if track count hasnt changed. Use a check sum)
- Save a correct file type
- Add metadata
- - correct track artists
- Soundcloud: Flag premium tracks (that will only be 29s long but could be misleading)
- Last sync order - improvements


## Electron
- Optimise
- Tool Bar
- Tray Icons
- Investigate: Can you use the bundled FFMPEG that comes with electron/chromium?
- Proper Shutdown Backend.

## Docker
- Fix. Broken during electron refactor.

## Other
- Further, investigate and fix any potential cors

## Settings
- Dont override other settings when saving

## CI/CD
- ✅ Remove make dir
- ✅ Unit Tests
- Publish to Releases
- enable warnings as errors
- ✅ Version Number with Git link 
- Fix Mac Build
- Fix action triggers (specifically build)

## Unit Tests
- TrackManager
  - Test: Test for date limit and track limit for both spotify and soundcloud