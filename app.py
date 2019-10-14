#!flask/bin/python
# Python standard libraries
import code, os, json, datetime
from db import db
# Third party libraries
from flask import Flask, redirect, url_for, request, jsonify
from bson.json_util import dumps
from pymodm.connection import connect
from pymodm.errors import ValidationError
from pymongo.errors import DuplicateKeyError
# Connect to MongoDB and call the connection "onx".
connect("mongodb://localhost:27017/onx", alias="onx-app")

# from api.user_controller import *
from app.models.user import *

app = Flask(__name__)

@app.route("/user/create", methods=['POST'])
def create_user():
    params = request.get_json()
    # code.interact(local=dict(globals(), **locals()))
    try:
        user = User(params['email'], params['name'], params['mobileNo'], params['role'])
        user.save(force_insert=True)
    except (DuplicateKeyError, ValidationError) as e:
        return jsonify({'Error':str(e)})
    return jsonify({'message':json.dumps(user.to_son().to_dict())})

@app.route("/users", methods=['GET','POST'])
def get_all_users():
    users_list = []
    for user in User.objects.all():
        users_list.append({'name':user.name, 'email':user.email, 'mobileNo':user.mobileNo, 'role':user.role,})
    return jsonify(users_list)

@app.route("/user/update/<string:email>", methods=['PATCH'])
def update_user(email):
    update_params = {}
    valid_params = ['name', 'mobileNo', 'role']
    for key, value in request.get_json().items():
        if key in valid_params:
            update_params[key] = value
    try:
        user = User.from_document(update_params)
        user.clean_fields(exclude=['email'])
        User.objects.raw({'_id':email}).update({'$set': update_params})
        # code.interact(local=dict(globals(), **locals()))
    except (User.DoesNotExist, ValidationError) as e:
        return jsonify({'Error': str(e)})
    return jsonify({"message":"User updated successfully."})

@app.route("/user/delete/<string:email>", methods=['DELETE'])
def delete_user(email):
    try:
        User.objects.get({'_id':email}).delete()
    except User.DoesNotExist:
        return jsonify({'Error':'User does not exists.'})
    return jsonify({'message':"User deleted from database."})

if __name__ == '__main__':
    app.run(debug=True, port=3000, ssl_context="adhoc")
