import sys
import os
import importlib

def print_debug_info():
    """ Test function for debugging purposes """
    print("Python executable:", sys.executable)
    print("Script:", sys.argv[0])
    print("Current working directory:", os.getcwd())
    print("Current file (__file__):", __file__)
    print("\nsys.path entries:")
    for path in sys.path:
        print("   ", path)

    def get_base_path():
        if getattr(sys, 'frozen', False):
            print("frozen")
            base_path = os.path.join(sys._MEIPASS, "../")  # When running as an executable from /dist/pysync-hub-backend/_internal
        else:
            base_path = os.path.abspath(".")
        return base_path

    print(get_base_path())

def check_module(module_name):
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            print(f"\nModule '{module_name}' not found.")
        else:
            print(f"\nModule '{module_name}' found at: {spec.origin}")
    except Exception as e:
        print(f"\nError checking module {module_name}: {e}")


from app.extensions import socketio
from app import create_app
from config import Config

app = create_app(Config)

if __name__ == '__main__':
    print("starting server")
    print_debug_info()
    socketio.run(app, debug=True)

# python -m flask run --debug
# pyinstaller --console --name pysync-hub-backend run.py
# pyinstaller pysync-hub-backend.spec
