<div align="center">
    <img src="src/frontend-react/public/images/icon.png" alt="PySync Hub" style="width:30%; height:auto;">

<h1><b>PySync DJ Hub</b></h1>
<strong> Automated DJ Music Library Manager Tool</strong>
</div>

PySync DJ Hub is a desktop app that allows you to seamlessly sync your playlists from multiple music platforms to your Rekordbox library. This tool streamlines the laborious task of DJ library management and lets you get straight to mixing music!

<div align="center">
    <img src="docs/images/pysync-29-04-25-home.png" alt="PySync Hub" style="width:80%; height:auto;">
</div>
<br>



### **Ethos:** 
This app is built with the hope that more people take up DJing and more people get into dance music. Having music to play is often a barrier to entry for this. All audio sourced from publicly available sources, such as youtube. Hence, the quality of audio sourced by this app is capped at a lower quality. Full quality tracks **please buy the music you love and support the artists. The dance music scene is dying, and it needs everyone's support.**

### **Features:**
- Seamless automated syncing of playlists between platforms such as SoundCloud and Spotify.
- Easily export playlists into Rekordbox.
- Organise your playlists with folders and a intuitive drag and drop interface.
- Intelligent downloads avoids duplicate track downloads saving storage space and time.   
- Stand-alone desktop app or in browser interface.
- Support for Spotify, Soundcloud, and soon Youtube.

### **How it works:** 
The program has three main stages: 
1. The first, adding playlists. This step involves querying the music platforms API's for your playlists information and adding them to the local database. 
2. The second stage is syncing the playlists. This step involves downloading the tracks from public sources, such as YouTube, using a Python library called yt-dlp. 
3. The final stage is exporting the playlists to Rekordbox. This step involves generating an iTunes XML file that can be imported into Rekordbox.  

### **Technical Details:** 
This app is built with Flask (Python) backend, React (Javascript) frontend, and a SQLite database. It has been bundled with Electron js to allow it to be run on desktop. Read more here [Technical Details](src/Readme.md)

# Demo

Demonstration of a simple user flow: Adding a playlist, dragging and dropping in the right folder, syncing and downloading the playlist, before lastly exporting to Rekordbox. [HD Demo Video Link](docs/PySync%20Hub%20Demo.mp4)

![Demo Gif](docs/PySync%20Hub%20Demo.gif)

The exported playlists then now visible in Rekordbox: 

![Exported Tracks In Rekordbox](docs/images/Exported-Tracks-Rekordbox.png)

# Getting Started


## Installation & Updating

See Install and Update guide here: [Install](docs/Install.md)

Alternatively PySync Hub can be run with a docker container, [docker instructions here](<How To Run Program in Docker.md>).

## How To Use

See the Help Page for all usage instructions: [Help](docs/Help.md)

## Troubleshooting
If you are having trouble with the app, please check the [Troubleshooting Section](docs/Help.md#troubleshooting) for common issues and solutions.

