#!flask/bin/python
from flask import Flask
from flask import request, jsonify
import json
# from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
client = MongoClient()
db = client.mydb

# app.config["MONGO_URI"] = "mongodb://localhost:27017/mydb"
# mongo = PyMongo(app)
# db = mongo.db

@app.route('/', methods=['GET'])
def home():
    return 'hello'


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


if __name__ == '__main__':
    app.run(debug=True)

