from app import create_app
from app.extensions import socketio
from config import Config

app = create_app(Config)

if __name__ == '__main__':
    socketio.run(app, debug=True)

# pyinstaller --console --name pysync-hub-backend run.py