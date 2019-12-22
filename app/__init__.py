from flask import Blueprint
from app.api.user import main as user
from app.api.session import main as session
from app.api.message import main as message
from app.api.corporate_group import main as corporate_group
from app.api.activity import main as activity
from app.api import app, socketio

app.register_blueprint(user) # For registering User APIs.
app.register_blueprint(session) # For registering Session APIs.
app.register_blueprint(message) # For registering Message APIs.
app.register_blueprint(activity) # For registering Activity APIs.
app.register_blueprint(corporate_group) # For registering Corporate Group APIs.
