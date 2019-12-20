from flask import Blueprint
from app.api.user import main
from app.api.session import main
from app.api.message import main
from app.api.corporate_group import main
from app.api.activity import main
from app.api import app, socketio

app.register_blueprint(api.user.main) # For registering User APIs.
app.register_blueprint(api.session.main) # For registering Session APIs.
app.register_blueprint(api.message.main) # For registering Message APIs.
app.register_blueprint(api.activity.main) # For registering Activity APIs.
app.register_blueprint(api.corporate_group.main) # For registering  Corporate Group APIs.