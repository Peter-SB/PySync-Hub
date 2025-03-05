# How to Start Program (with Docker)

## Installing Docker

### For Mac
1. Download Docker Desktop for Mac from the [Docker website](https://www.docker.com/products/docker-desktop).
2. Open the downloaded `.dmg` file and drag the Docker icon to the Applications folder.
3. Launch Docker from the Applications folder.

### For Windows
1. Download Docker Desktop for Windows from the [Docker website](https://www.docker.com/products/docker-desktop).
2. Run the installer and follow the on-screen instructions.
3. **After installation, launch Docker Desktop from the Start menu.

## Building and Running Containers

1. Make sure Docker or Docker Desktop is running.
2. First, in the PySync-Hub folder, run this command to start the program. (This can take a minute or two to build and start.) 
```
docker-compose up --build
```
3. Check Docker Desktop to see it running.
4. Go to [localhost:3000](http://localhost:3000/) if it doesnt automatically start.

run this to shutdown the program:
```
docker-compose down
```

For more detailed instructions, refer to the [Docker documentation](https://docs.docker.com/get-started/).