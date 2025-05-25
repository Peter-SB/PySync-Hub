FROM python:3.13-slim

WORKDIR /PySync-Hub

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/PySync-Hub

# Install necessary dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    xz-utils \
    ca-certificates \
    curl &&\
    rm -rf /var/lib/apt/lists/*

# Install standalone FFmpeg and FFprobe binaries
RUN mkdir -p /ffmpeg && \
    curl -L -o /ffmpeg/ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz && \
    tar -xf /ffmpeg/ffmpeg.tar.xz --strip-components=1 -C /ffmpeg && \
    rm /ffmpeg/ffmpeg.tar.xz && \
    chmod +x /ffmpeg/ffmpeg /ffmpeg/ffprobe

# Add FFmpeg and FFprobe to the system PATH
ENV PATH="/ffmpeg:${PATH}"

# Copy requirements and install dependencies
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directory for database
#RUN mkdir -p instance

# Expose Flask-SocketIO port
EXPOSE 5000

# Run the application with Gunicorn and eventlet for Flask-SocketIO support
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "app.run:app"]


