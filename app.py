#!flask/bin/python
from flask import Flask
from flask import request, jsonify
import json
# from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
app.debug = True
socketio = SocketIO(app, cors_allowed_origins="*")
client = MongoClient()
db = client.mydb

# app.config["MONGO_URI"] = "mongodb://localhost:27017/mydb"
# mongo = PyMongo(app)
# db = mongo.db


@app.route('/test', methods=['GET'])
def test():
    users = db.users.find()
    output = []
    for s in users:
        output.append({'name' : s['name'], 'email' : s['email']})
    return jsonify({'result' : output})

@app.route('/createSession', methods=['POST'])
def createSession():
    params = request.get_json()

    doc_id = db.sessions.insert({
        "type": params['type'],
        "userId": params['userId'],
        "username": params['username'],
        "requestedAt": params['requestedAt'],
        "status": params['status'],
    })
    return str(doc_id)

@app.route('/updateSession', methods=['POST'])
def updateSession():
    params = request.get_json()

    sessionId = params['sessionId']

    response = db.sessions.update({ "_id": ObjectId(sessionId) }, {'$set': {
        "status": params['status'],
        "mentorname": params['mentorname'],
        "mentorId": params['mentorId']
    }})
    if (response['updatedExisting']):
        return 'updated'
    else:
        return 'error'

@app.route('/sendMessage', methods=['POST'])
def sendMessage():
    params = request.get_json()

    doc_id = db.messages.insert({
        "sessionId": params['sessionId'],
        "senderId": params['senderId'],
        "message": params['message'],
        "timeStamp": params['timeStamp'],
    })
    return str(doc_id)

@app.route('/fetchMessages', methods=['POST'])
def fetchMessages():
    params = request.get_json()

    messages = db.messages.find({
        "sessionId": params['sessionId']
    })
    output = []
    for msg in messages:
        output.append({
            'message': msg['message'],
            'senderId': msg['senderId'],
            'timeStamp': msg['timeStamp'],
        })
    return jsonify({'result' : output})

@app.route('/', methods=['GET'])
def home():
    # send('channel2', 'MSg from server')
    # send('helloo from server')
    return 'hello'

@socketio.on('message')
def handle_message(msg):
    print('msg recieved' + msg)
    # send('msg recieved' + msg)

@socketio.on('qqq')
def onTest(message):
    print('received message on qqq: ' + message)

@socketio.on('connect')
def test_connect():
    print("client connected")


if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app)

