#!flask/bin/python
from flask import Flask
from flask import request, jsonify
from flask_pymongo import PyMongo

from models.user import User

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/mydb"
mongo = PyMongo(app)
db = mongo.db

@app.route('/')
def home():
    return 'hello'


@app.route('/test', methods=['POST'])
def test():
    request_data = request.get_json()
    user = User(**request_data)
    db.users.insert_one(user.asdict())
    return jsonify(user.asdict())

if __name__ == '__main__':
    app.run(debug=True,port=300)

