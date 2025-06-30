# Multi-stage Dockerfile for building and running PySync-Hub in a container.

# ----------------------------------------
# Stage 1: Build the React frontend static files
# ----------------------------------------
FROM node:16-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend-react/package*.json ./
RUN npm ci

COPY frontend-react/ ./
# disable CI-specific behavior
ENV CI=false
RUN npm run build

# ----------------------------------------
# Stage 2: Install Flask backend & assemble
# ----------------------------------------
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Install FFmpeg and FFprobe binaries
RUN mkdir -p /ffmpeg && \
    curl -L -o /ffmpeg/ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz && \
    tar -xf /ffmpeg/ffmpeg.tar.xz --strip-components=1 -C /ffmpeg && \
    rm /ffmpeg/ffmpeg.tar.xz && \
    chmod +x /ffmpeg/ffmpeg /ffmpeg/ffprobe

# Add FFmpeg and FFprobe to the system PATH
ENV PATH="/ffmpeg:${PATH}"

# install Python requirements
COPY backend-flask/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy backend source
COPY backend-flask/ ./

# pull in the built React static files
COPY --from=frontend-builder /app/frontend/build ./build

EXPOSE 5000
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "run:app"]
