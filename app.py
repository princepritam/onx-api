#!flask/bin/python
# Python standard libraries
import code, os, json, datetime
from db import db
# Third party libraries
from flask import Flask, redirect, url_for, request, jsonify
from bson import ObjectId, errors
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
    try:
        user = User(email=params['email'], name=params['name'], mobileNo=params['mobileNo'],
                    role=params['role'], created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())
        user.save(force_insert=True)
    except (DuplicateKeyError, ValidationError) as e:
        return jsonify({'Error': str(e), 'error_status': True})
    return jsonify({'Message': 'Successfully created user.','error_status': False})

@app.route("/users", methods=['GET','POST'])
def get_all_users():
    users_list = []
    for user in User.objects.all():
        users_list.append({'id': str(user._id), 'name':user.name, 'email':user.email, 
                                'mobileNo':user.mobileNo, 'role':user.role, 'created_at':user.created_at, 'updated_at':user.updated_at})
    return jsonify(users_list)

@app.route("/user/<string:id>", methods=['GET'])
def show_user(id):
    try:
        id = ObjectId(id)
        user = User.objects.get({'_id': id})
        return jsonify([{'id': str(user._id), 'name':user.name, 'email':user.email, 
                        'mobileNo':user.mobileNo, 'role':user.role, 'created_at':user.created_at, 'updated_at':user.updated_at}])
    except (User.DoesNotExist, errors.InvalidId) as e :
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'Error': message, 'error_status': True})


@app.route("/user/update/<string:id>", methods=['PATCH'])
def update_user(id):
    try:
        id = ObjectId(id)
        update_params = {}
        valid_params = ['name', 'mobileNo', 'role', 'email']
        for key, value in request.get_json().items():
            if key in valid_params:
                update_params[key] = value
        User.objects.get({'_id':id})
        user = User.from_document(update_params)
        user.full_clean(exclude=None)
        update_params['updated_at'] = datetime.datetime.now()
        User.objects.raw({'_id': id}).update({'$set': update_params})
    except (User.DoesNotExist, ValidationError, errors.InvalidId) as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        # code.interact(local=dict(globals(), **locals()))
        return jsonify({'Error': message, 'error_status': True})
    return jsonify({'Message': 'User updated successfully.', 'error_status': False})

@app.route("/user/delete/<string:id>", methods=['DELETE'])
def delete_user(id):
    try:
        id = ObjectId(id)
        User.objects.get({'_id':id}).delete()
    except (User.DoesNotExist, errors.InvalidId) as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'Error': message, 'error_status': True})
    return jsonify({'Message': 'User deleted from database.', 'error_status': False})

#CRUD for Session
@app.route("/session/create", methods=['POST'])
def create_session():
    create_params = request.get_json()
    try:
        mentor = User.objects.get({'_id': ObjectId(create_params['mentor_id'])})
        student = User.objects.get({'_id': ObjectId(create_params['student_id'])})
        session = Session(type_=create_params['type'], mentor=mentor, student=student, created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())
        session.save(force_insert=True)
    except(User.DoesNotExist, ValidationError) as e:
        return jsonify({'Error': str(e), 'error_status': True})
    return jsonify({'Message': 'Successfully created session.','error_status': False})

@app.route("/sessions", methods=['GET', 'POST'])
def get_all_Sessions():
    sessions_list = []
    for session in Session.objects.all():
        sessions_list.append({'id': str(session._id), 'type': session.type_, 'mentor': session.mentor.email, 'student': session.student.email, 'start_time':
                    session.start_time, 'status': session.status, 'duration': session.duration, 'end_time': session.end_time,
                    'feedback': session.feedback, 'created_at': session.created_at, 'updated_at': session.updated_at})
    return jsonify(sessions_list)

@app.route("/update/session/<string:id>", methods=['POST'])
def update_session(id):
    try:
        id = ObjectId(id)
        code.interact(local=dict(globals(), **locals()))
        session = Session.objects.get({'_id': id})
    except(Session.DoesNotExist) as e :
        return jsonify({'Error': str(e), 'error_status': True})
    return jsonify({'Message': 'Successfully updated session.','error_status': False})




if __name__ == '__main__':
    app.run(debug=True, port=3000, ssl_context="adhoc")
