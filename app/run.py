from app import create_app
from app.extensions import socketio
from app.config import Config

app = create_app(Config)

if __name__ == '__main__':
    socketio.run(app, debug=True)
    input("Press Enter to exit...")

# pyinstaller --console --name pysync-hub-backend run.py