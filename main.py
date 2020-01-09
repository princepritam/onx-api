from pymodm.connection import connect
from app import app, socketio, celery_client

deploy = "mongodb://testuser:qwerty123@ds241258.mlab.com:41258/heroku_mjkv6v40"
local = "mongodb://localhost:27017/onx"

connect(local, alias="onx-app", retryWrites=False)

app.config['SECRET_KEY'] = 'unxunxunx'

# Health check
@app.route("/ping", methods=['GET'])
def home():
    return 'Hello! Your app is up and running.'

@socketio.on('custom')
def handle_my_custom_event(json):
    socketio.emit('custom', json)
    
if __name__ == '__main__':
    # socketio.run(app)
    app.run(port=3000, debug=True, host='localhost')