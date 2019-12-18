from flask import Flask, Blueprint
from flask_socketio import SocketIO
from app.api.user import main
from app.api.session import main
from app.api.message import main
from app.api.corporate_group import main
from app.api.activity import main

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

app.register_blueprint(api.user.main)
app.register_blueprint(api.session.main)
app.register_blueprint(api.message.main)
app.register_blueprint(api.activity.main)
app.register_blueprint(api.corporate_group.main)