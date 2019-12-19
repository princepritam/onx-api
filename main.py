from flask import Blueprint, Flask, request, jsonify
from pymodm.connection import connect
from app import app, socketio

deploy = "mongodb://testuser:qwerty123@ds241258.mlab.com:41258/heroku_mjkv6v40"
local = "mongodb://localhost:27017/onx"

connect(deploy, alias="onx-app", retryWrites=False)

app.config['SECRET_KEY'] = 'unxunxunx'

# Health check
@app.route("/ping", methods=['GET'])
def home():
    return 'Hello! Your app is up and running.'

if __name__ == '__main__':
    socketio.run(app)
    # app.run(port=3000, debug=True, host='localhost')