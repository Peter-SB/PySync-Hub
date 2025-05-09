⚠️ This Is A WIP Project, and is indented for personal skill development only. While not intended for public use, the aim of the project was to expand my technical ability and further practice developing apps with a seamless (hypothetical) user-experience in-mind.  

# PySync DJ Hub

PySync DJ Hub is a desktop app that allows you to seamlessly sync your playlists from multiple music platforms to your Rekordbox library. It supports currently supports Spotify, Soundcloud, and soon Youtube.

<div align="center">
    <img src="docs/images/pysync-29-04-25-home.png" alt="PySync Hub" style="width:80%; height:auto;">
</div>

**Ethos:** This app is built with the hope that more people take up DJing and get more people get into dance music. The quality of audio downloaded by this app is capped at 128kbps and all audio sourced from publicly available sources. **Please buy the music your love and support the artists. The music scene is dying, and it needs everyone's support.**

**Features:**
- Seamless automated syncing of playlists between platforms such as SoundCloud and Spotify.
- Easily export playlists into Rekordbox.
- Organise your playlists with folders and a intuitive drag and drop interface.
- Intelligent downloads avoids duplicate track downloads saving storage space and time.   
- Standalone desktop app or in browser interface.

**How it works:** The program has three main stages. The first, adding playlists. This step involves querying the music platforms API's for your playlists information and adding them to the local database. The second stage is syncing the playlists. This step involves downloading the tracks from public sources, such as YouTube, using a Python library called yt-dlp. The final stage is exporting the playlists to Rekordbox. This step involves generating an iTunes XML file that can be imported into Rekordbox.  

**Technical Details:** This app is built with Flask (Python) backend, React (Javascript) frontend, and a SQLite database. It has been bundled with Electron js to allow it to be run on desktop. Read more here [Technical Details](docs/TechnicalReadme.md)

# Getting Started


## Installation

See Install and Update guide here: [Install](docs/Install.md)

## How To Use

See the Help Page for all usage instructions: [Help](docs/Help.md)

## Troubleshooting
If you are having trouble with the app, please check the [troubleshooting page](docs/Help.md) for common issues and solutions.

