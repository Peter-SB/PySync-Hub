## Stage 1: Build React frontend
#FROM node:20-alpine AS frontend-builder
#WORKDIR /app/src/frontend-react
#COPY src/frontend-react/package*.json ./
#RUN npm ci
#COPY src/frontend-react ./
#RUN npm run build
#
## Stage 2: Build backend and assemble final image
#FROM python:3.13-slim
#WORKDIR /PySync-Hub
#
## Set environment variables
#ENV PYTHONDONTWRITEBYTECODE 1
#ENV PYTHONUNBUFFERED 1
#ENV PYTHONPATH=/PySync-Hub
#
## Install necessary dependencies
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    gcc \
#    python3-dev \
#    xz-utils \
#    ca-certificates \
#    curl &&\
#    rm -rf /var/lib/apt/lists/*
#
## Install standalone FFmpeg and FFprobe binaries
#RUN mkdir -p /ffmpeg && \
#    curl -L -o /ffmpeg/ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz && \
#    tar -xf /ffmpeg/ffmpeg.tar.xz --strip-components=1 -C /ffmpeg && \
#    rm /ffmpeg/ffmpeg.tar.xz && \
#    chmod +x /ffmpeg/ffmpeg /ffmpeg/ffprobe
#
## Add FFmpeg and FFprobe to the system PATH
#ENV PATH="/ffmpeg:${PATH}"
#
## Copy requirements and install dependencies
#COPY ../requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt
#
## Copy backend code
#COPY . .
#
## Copy built React frontend into backend static/build directory
#COPY --from=frontend-build /frontend/build ./build
#
## Expose Flask-SocketIO port (backend API/UI)
#EXPOSE 5000
#
## Run the application with Gunicorn and eventlet for Flask-SocketIO support
#CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "app.run:app"]
#
#


## Stage 1: Build the React frontend
#FROM node:16-alpine AS frontend-builder
#
## Set working directory
#WORKDIR /app/frontend
#
## Copy package files and install dependencies
#COPY frontend-react/package*.json ./
#RUN npm ci
#
## Copy the rest of the frontend source and build
#COPY frontend-react/ ./
## Prevent CI env interfering with build
#ENV CI=false
#RUN npm run build
#
## Stage 2: Build the Flask backend and assemble final image
#FROM python:3.11-slim
#
## Install system dependencies (if any)
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    build-essential \
#    && rm -rf /var/lib/apt/lists/*
#
## Set working directory for backend
#WORKDIR /app/backend
#
## Copy and install Python dependencies
#COPY backend-flask/requirements.txt ./
#RUN pip install --no-cache-dir -r requirements.txt
#
## Copy backend source
#COPY backend-flask/ ./
#
## Copy React build artifacts into Flask static folder (or wherever your app serves them)
## Adjust the target path if your Flask app expects build files in a different location
#COPY --from=frontend-builder /app/frontend/build ./build
#
## Expose the Flask-SocketIO port
#EXPOSE 5000
#
## Run the application with Gunicorn and eventlet for Flask-SocketIO support
#CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "app.run:app"]

# src/Dockerfile

# ───────────────────────────────────────────────
# Stage 1: build the React frontend
# ───────────────────────────────────────────────
FROM node:16-alpine AS frontend-builder

# install deps & build
WORKDIR /app/frontend
COPY frontend-react/package*.json ./
RUN npm ci

COPY frontend-react/ ./
# disable CI-specific behavior
ENV CI=false
RUN npm run build


# ───────────────────────────────────────────────
# Stage 2: install Flask backend & assemble
# ───────────────────────────────────────────────
FROM python:3.11-slim

# install any OS-level build tools you need
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# install Python requirements
COPY backend-flask/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy backend source
COPY backend-flask/ ./

# pull in the built React app
COPY --from=frontend-builder /app/frontend/build ./build

# expose your Flask-SocketIO port
EXPOSE 5000

# run under Gunicorn+eventlet
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "run:app"]
