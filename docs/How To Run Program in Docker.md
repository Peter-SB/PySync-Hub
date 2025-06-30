# How to Run The Program with Docker

Instead of running the program with the platform native executable, you can build and run this as a docker image. This is particularly useful if you want to host PySync remotely and expose the UI to allow for remote library management.

```
cd src/
docker build -t pysync-hub-build .
docker run \\
    --name pysync-hub \\
    -p 5000:5000 \\
    -v "${PWD}\..\music_downloads:/music_downloads" \\
    -v "${PWD}\..\rekordbox_library_exports:/rekordbox_library_exports" \\
    -v "${PWD}\..\database.db:/database.db" \\
    pysync-hub-build
```

or

```
cd src/
docker build -t pysync-hub-build .
docker run `
    --name pysync-hub `
    -p 5000:5000 `
    -v "${PWD}\..\music_downloads:/music_downloads" `
    -v "${PWD}\..\rekordbox_library_exports:/rekordbox_library_exports" `
    -v "${PWD}\..\database.db:/database.db" `
    -v "${PWD}\..\settings.yml:/settings.yml" `
    pysync-hub-build
```

## Notes

- The DockerFile is in `src/Dockerfile`.

- Backend url is set to `http://127.0.0.1:5000` in `src/frontend-react/src/config.js`.
