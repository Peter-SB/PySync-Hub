# Development Setup Guide

Follow these steps to set up your development environment for the PySync Hub project after pulling the repository.

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
   - Follow the instructions in [src/ffmpeg/ReadMe.md](src/ffmpeg/ReadMe.md) to download and place the binaries in the `src/ffmpeg/` directory.

---

## Running the Application

### Using Docker
1. Start the application:
   ```bash
   docker-compose up --build
   ```
2. Access the app at [http://localhost:3000](http://localhost:3000).

3. Stop the application:
   ```bash
   docker-compose down
   ```

### Without Docker
1. Build the React frontend:
   ```bash
   cd src/frontend-react
   npm run build
   cd ../..
   ```

2. Start the Electron app:
   ```bash
   npm run start
   ```

---

## Additional Notes

- For CI/CD setup, refer to the `.github/workflows/` directory.
- For troubleshooting, consult the [docs/Todo.md](docs/Todo.md) file.

```// filepath: e:\Code\Python\PySync-Hub\DevelopmentSetup.md
# Development Setup Guide

Follow these steps to set up your development environment for the PySync Hub project after pulling the repository.

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
   - Follow the instructions in [src/ffmpeg/ReadMe.md](src/ffmpeg/ReadMe.md) to download and place the binaries in the `src/ffmpeg/` directory.

---

## Running the Application

### Using Docker
1. Start the application:
   ```bash
   docker-compose up --build
   ```
2. Access the app at [http://localhost:3000](http://localhost3000).

3. Stop the application:
   ```bash
   docker-compose down
   ```

### Without Docker
1. Build the React frontend:
   ```bash
   cd src/frontend-react
   npm run build
   cd ../..
   ```

2. Start the Electron app:
   ```bash
   npm run start
   ```

---

## Additional Notes

- For CI/CD setup, refer to the `.github/workflows/` directory.
- For troubleshooting, consult the [docs/Todo.md](docs/Todo.md) file.
