from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")

emit = emit