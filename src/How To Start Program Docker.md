# How to Start Program (with Docker)

1. Download Docker Desktop  from the [Docker website](https://www.docker.com/products/docker-desktop).
2. Install.
3. After installation, launch Docker Desktop.

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