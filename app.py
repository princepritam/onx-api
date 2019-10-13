#!flask/bin/python
# Python standard libraries
import json
import os
import code
from db import db
# Third party libraries
from flask import Flask, redirect, url_for, request, jsonify

from pymodm.connection import connect
from pymodm.errors import ValidationError
# Connect to MongoDB and call the connection "onx".
connect("mongodb://localhost:27017/onx", alias="onx-app")

# from api.user_controller import *
from app.models.user import *

app = Flask(__name__)

@app.route("/user/create", methods=['POST'])
def create_user():
    params = request.get_json()
    try:
        for user in User.objects.all():
            if params['email'] == user.email:
                raise ValidationError("User already exists.")
        user = User(params['email'], params['name'], params['mobileNo'], params['role'])
        user.save()
    except ValidationError as e:
        return jsonify({'Error':str(e)})
    return jsonify({'message':json.dumps(user.to_son().to_dict())})

@app.route("/users", methods=['GET','POST'])
def get_all_users():
    users_list = []
    for user in User.objects.all():
        users_list.append({'name':user.name, 'email':user.email, 'mobileNo':user.mobileNo, 'role':user.role,})
    return jsonify(users_list)

@app.route("/user/update/<string:email>", methods=['POST'])
def update_user(email):
    params = request.get_json()
    user = User.objects.raw({'email':email})
    # user

@app.route("/user/delete/<string:email>", methods=['POST'])
def delete_user(email):
    user_ = User.objects.raw({'email':email})
    # code.interact(local=dict(globals(), **locals()))
    db.user.delete_one({'email':email})
    return jsonify({'message':"User deleted from database"})

if __name__ == '__main__':
    app.run(debug=True, port=3000, ssl_context="adhoc")
