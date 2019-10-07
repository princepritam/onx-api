#!flask/bin/python
from flask import Flask
from flask import request, jsonify
import json
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/mydb"
mongo = PyMongo(app)
db = mongo.db

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


if __name__ == '__main__':
    app.run(debug=True)

