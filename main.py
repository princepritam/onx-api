#!flask/bin/python
# Python standard libraries
import code, os, json, datetime

from flask import Flask, redirect, url_for, request, jsonify
from bson import ObjectId, errors
from pymodm.connection import connect
from pymongo.errors import DuplicateKeyError

deploy="mongodb://testuser:qwerty123@ds241258.mlab.com:41258/heroku_mjkv6v40"
# deploy="mongodb://heroku_mjkv6v40:osce9dakl9glgd4750cuovm8h1@ds241258.mlab.com:41258/heroku_mjkv6v40"
local="mongodb://localhost:27017/onx"

connect(deploy, alias="onx-app", retryWrites=False)

from app.models.models import *

app = Flask(__name__)

@app.route("/", methods=['GET'])
def home():
    return 'hello'



# APIs for User
@app.route("/user/create", methods=['POST'])
def create_user():
    params = request.get_json()
    try:
        user = User(email=params['email'], name=params['name'], mobileNo=params['mobileNo'],
                    role=params['role'], created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())
        user.save(force_insert=True)
    except Exception as e:
        return jsonify({'Error': str(e), 'error_status': True})
    return jsonify({'Message': 'Successfully created user.','user_id': str(user._id), 'error_status': False})

@app.route("/users", methods=['GET','POST'])
def get_all_users():
    users_list = []
    for user in User.objects.all():
        users_list.append({'id': str(user._id), 'name':user.name, 'email':user.email, 
                                'mobileNo':user.mobileNo, 'role':user.role, 'created_at':user.created_at, 'updated_at':user.updated_at})
    return jsonify(users_list)

@app.route("/user", methods=['GET'])
def show_user():
    try:
        user_id = ObjectId(request.get_json()['user_id'])
        user = User.objects.get({'_id': user_id})
        return jsonify([{'id': str(user._id), 'name':user.name, 'email':user.email, 
                        'mobileNo':user.mobileNo, 'role':user.role, 'created_at':user.created_at, 'updated_at':user.updated_at}])
    except Exception as e :
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'Error': message, 'error_status': True})


@app.route("/user/update", methods=['PATCH'])
def update_user():
    try:
        user_id = ObjectId(request.get_json()['user_id'])
        User.objects.get({'_id': user_id}) #validates if given user id is valid.
        update_params = {}
        valid_params = ['name', 'mobileNo', 'role']
        for key, value in request.get_json().items():
            if key in valid_params:
                update_params[key] = value
        user = User.objects.raw({'_id': user_id})
        user_valid = User.from_document(update_params) #validate update params
        user_valid.full_clean(exclude=None) #validate update params and raise exception if any
        update_params['updated_at'] = datetime.datetime.now()
        user.update({'$set': update_params})
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'Error': message, 'error_status': True})
    return jsonify({'Message': 'User updated successfully.', 'error_status': False})

@app.route("/user/delete", methods=['DELETE'])
def delete_user():
    try:
        user_id = ObjectId(request.get_json()['user_id'])
        User.objects.get({'_id': user_id}).delete()
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'Error': message, 'error_status': True})
    return jsonify({'Message': 'User deleted from database.', 'error_status': False})



# APIs for Session
@app.route("/session/create", methods=['POST'])
def create_session():
    create_params = request.get_json()
    try:
        mentor = User.objects.get({'_id': ObjectId(create_params['mentor_id'])})
        session = Session(type_=create_params['type'], mentor=mentor, members=create_params['members'], created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())
        session.save(force_insert=True)
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'Error': message, 'error_status': True})
    return jsonify({'Message': 'Successfully created session.', 'session_id': str(session._id), 'error_status': False})

@app.route("/sessions", methods=['GET'])
def get_all_sessions():
    sessions_list = []
    for session in Session.objects.all():
        sessions_list.append({'id': str(session._id), 'type': session.type_, 'mentor': str(session.mentor._id), 'members': session.members, 'start_time':
                    session.start_time, 'status': session.status, 'duration': session.duration, 'end_time': session.end_time,
                    'feedback': session.feedback, 'created_at': session.created_at, 'updated_at': session.updated_at})
    return jsonify(sessions_list)

@app.route("/session", methods=['GET'])
def show_session():
    try:
        session_id = ObjectId(request.get_json()['session_id'])
        session = Session.objects.get({"_id": session_id})
        result = {'Session': {'id': str(session._id), 'type': session.type_, 'mentor': str(session.mentor._id), 'members': session.members, 'start_time':
                    session.start_time, 'status': session.status, 'duration': session.duration, 'end_time': session.end_time,
                    'feedback': session.feedback, 'created_at': session.created_at, 'updated_at': session.updated_at}}
        return jsonify(result)
    except Exception as e:
        message = 'Session does not exists.' if str(e) == '' else str(e)
        return jsonify({'Error': message, 'error_status': True})

@app.route("/session/update", methods=['PATCH'])
@app.route("/session/update/<string:action>", methods=['PATCH'])
def update_session(action=None):
    try:
        update_params = request.get_json()
        session_id = ObjectId(update_params['session_id'])
        session_ = Session.objects.get({'_id': session_id}) # validates if given session id is valid.
        session = Session.objects.raw({'_id': session_id})
        if action == "start" and session_.status == 'inactive':
            session.update({'$set': {"start_time": datetime.datetime.now(), 'status': 'active'}})
        elif action == "end" and session_.status == 'active':
            end_time = datetime.datetime.now()
            seconds = (end_time - session_.start_time).total_seconds()
            hours = int(seconds // 3600)
            # code.interact(local=dict(globals(), **locals()))
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            duration = '{}:{}:{}'.format(hours, minutes, secs)
            session.update({'$set': {"end_time": datetime.datetime.now(), 'status': 'ended', 'duration': duration}})
        else:
            raise ValidationError("Presently the session is " + session_.status)
    except Exception as e :
        message = 'Session does not exists.' if str(e) == '' else str(e)
        return jsonify({'Error': message, 'error_status': True})
    return jsonify({'Message': 'Successfully updated session.','error_status': False})




# APIs for Message
@app.route("/message/create", methods=['POST'])
def create_message():
    try:
        create_params = request.get_json()
        create_params['created_at'] = datetime.datetime.now()
        message = Message(session=create_params['session_id'], sender=create_params['sender_id'],
                        content=create_params['content'], type_=create_params['type_'], created_at=create_params['created_at'])
        message.save()
    except Exception as e:
        return jsonify({"Error": str(e), 'error_status': True})
    return jsonify({'Message': 'Successfully created a message.','error_status': False})

@app.route("/messages", methods=['GET'])
def get_messages():
    try:
        session_id = ObjectId(request.get_json()['session_id'])
        session = Session.objects.get({'_id': session_id})
        result = []
        messages = Message.objects.raw({'session': session_id})
        for message in messages:
            user = message.sender
            sender_details = {"id": str(user._id), "name": user.name, "email": user.email, "role": user.role}
            result.append({"id": str(message._id), "session_id": str(message.session._id), "sender": sender_details,
            "content": message.content, "type": message.type_, "created_at":message.created_at})
    except Exception as e:
        message = 'Session does not exists.' if str(e) == '' else str(e)
        return jsonify({'Error': message, 'error_status': True})
    return jsonify({'Messages': result, 'error_status': False})



if __name__ == '__main__':
    app.run()
