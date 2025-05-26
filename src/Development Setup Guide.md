# Development Setup Guide

Follow these steps to set up your development environment.

---

## Prerequisites

Ensure the following tools are installed on your system:

1. **Node.js** (v16 or higher)
   - [Download Node.js](https://nodejs.org/)
   - Verify installation:
     ```bash
     node -v
     npm -v
     ```

2. **Python** (v3.11)
   - [Download Python](https://www.python.org/downloads/)
   - Verify installation:
     ```bash
     python --version
     pip --version
     ```

3. **Docker** (Optional, for Docker-based setup)
   - [Download Docker](https://www.docker.com/products/docker-desktop)
   - Verify installation:
     ```bash
     docker --version
     docker-compose --version
     ```

4. **Git**
   - [Download Git](https://git-scm.com/)
   - Verify installation:
     ```bash
     git --version
     ```

5. **Full Command**:
    ```bash
    node -v
    npm -v
    python --version
    pip --version     
    ```

---

## Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/PySync-Hub.git
   cd PySync-Hub
   ```

2. **Install Node.js Dependencies**
   ```bash
   cd src
   npm install
   cd frontend-react
   npm install
   cd ../..
   ```

3. **Install Python Dependencies**
   ```bash
   cd src/backend-flask
   pip install -r requirements.txt
   cd ../..
   ```

4. **Install FFmpeg and FFprobe** 
   - Follow the instructions in [src/ffmpeg/ReadMe.md](src\ffmpeg\ReadMe.md) to download and place the binaries in the `src/ffmpeg/` directory.

5. **Full Command**:
    ```bash
    cd src
    npm install
    cd frontend-react
    npm install
    cd ../..
    
    cd src/backend-flask
    pip install -r requirements.txt
    cd ../..
    ```

---


### Run In Development Mode

1. Start the Flask Server:
   ```bash
   cd src/backend-flask
   python -m flask run --debug
   ```

2. Build the React frontend:
    ```bash
    cd src/frontend-react
    npm run start
    cd ../..
    ```

---

## Additional Notes

- For CI/CD setup, refer to the `.github/workflows/` directory.