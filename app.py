#!flask/bin/python
# Python standard libraries
import code, os, json, datetime
from db import db
# Third party libraries
from flask import Flask, redirect, url_for, request, jsonify
from bson.json_util import dumps
from pymodm.connection import connect
from pymongo.errors import DuplicateKeyError
# Connect to MongoDB and call the connection "onx".
connect("mongodb://localhost:27017/onx", alias="onx-app")

# from api.user_controller import *
from app.models.user import *

app = Flask(__name__)

#CRUD operations on User

@app.route("/user/create", methods=['POST'])
def create_user():
    params = request.get_json()
    # code.interact(local=dict(globals(), **locals()))
    try:
        user = User(params['email'], params['name'], params['mobileNo'], params['role'], datetime.datetime.now())
        user.save(force_insert=True)
    except (DuplicateKeyError, ValidationError) as e:
        return jsonify({'Error': str(e), 'error_status': True})
    return jsonify({'Message': 'Successfully created user.','error_status': False})

@app.route("/users", methods=['GET','POST'])
def get_all_users():
    users_list = []
    for user in User.objects.all():
        users_list.append({'name':user.name, 'email':user.email, 'mobileNo':user.mobileNo, 'role':user.role, 'created_at':user.created_at, 'updated_at':user.updated_at})
    return jsonify(users_list)

@app.route("/user/update/<string:email>", methods=['PATCH'])
def update_user(email):
    update_params = {}
    valid_params = ['name', 'mobileNo', 'role', 'email']
    for key, value in request.get_json().items():
        if key in valid_params:
            update_params[key] = value
    try:
        User.objects.get({'email':email})
        user = User.from_document(update_params)
        user.full_clean(exclude=None)
        update_params['updated_at'] = datetime.datetime.now()
        User.objects.raw({'email':email}).update({'$set': update_params})
    except (User.DoesNotExist, ValidationError) as e:
        # code.interact(local=dict(globals(), **locals()))
        return jsonify({'Error': str(e), 'error_status': True})
    return jsonify({'Message': 'User updated successfully.', 'error_status': False})

@app.route("/user/delete/<string:email>", methods=['DELETE'])
def delete_user(email):
    try:
        User.objects.get({'email':email}).delete()
    except User.DoesNotExist:
        return jsonify({'Error': 'User does not exists.', 'error_status': True})
    return jsonify({'Message': 'User deleted from database.', 'error_status': False})

#CRUD for Session
@app.route("/session/create", methods=['POST'])
def create_session():
    params = request.get_json()



if __name__ == '__main__':
    app.run(debug=True, port=3000, ssl_context="adhoc")
