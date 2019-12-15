#!flask/bin/python
# Python standard libraries
import code
import os
import json
import datetime
import time

from flask import Flask, redirect, url_for, request, jsonify
from bson import ObjectId, errors
from pymodm.connection import connect
from pymongo.errors import DuplicateKeyError
from flask_socketio import SocketIO, emit
# from app.api.user import *
from app.models.message import *
from app.models.corporate_group import *
from app.models.activity import *
from threading import Timer

deploy = "mongodb://testuser:qwerty123@ds241258.mlab.com:41258/heroku_mjkv6v40"
# deploy="mongodb://heroku_mjkv6v40:osce9dakl9glgd4750cuovm8h1@ds241258.mlab.com:41258/heroku_mjkv6v40"
local = "mongodb://localhost:27017/onx"

connect(deploy, alias="onx-app", retryWrites=False)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'unxunxunx'
socketio = SocketIO(app, cors_allowed_origins="*")

expiry_timer = None

# Health check
@app.route("/ping", methods=['GET'])
def home():
    return 'Hello! Your app is up and running.'

# APIs for User
@app.route("/user/create", methods=['POST'])
def create_user():
    create_params = {}
    try:
        valid_params = ['name', 'role', 'email', 'user_token', 'photo_url']
        for key, value in request.get_json().items(): # validate update params
            if key in valid_params:
                create_params[key] = value
        user = User(
            name=create_params['name'],
            role=create_params['role'],
            email=create_params['email'],
            user_token=create_params['user_token'],
            photo_url=create_params['photo_url'],
            created_at=datetime.datetime.now().isoformat()
        )
        user.save(full_clean=True)
    except Exception as e:
        if str(e) == 'User with this email already exist':
            user_ = User.objects.get({'email': create_params['email']})
            return jsonify({
            'message': str(e),
            'error_status': False,
            'mentor_verified': user_.mentor_verified,
            'user_id': str(user_._id),
            'role': user_.role,
            'previously_logged_in': True}), 200
        return jsonify({'error': str(e), 'error_status': True}), 200
    return jsonify({'message': 'Successfully created user.', 'user_id': str(user._id), 'error_status': False}), 201


@app.route("/users", methods=['GET'])
def get_all_users():
    users_list = []
    for user in User.objects.all():
        user_group = None
        if user.user_group != None:
            user_group = CorporateGroup.objects.get({"_id": ObjectId(user.user_group)}).code
        users_list.append({
        'user_id': str(user._id),
        'name': user.name,
        'email': user.email,
        'mobile_no': user.mobile_no,
        'nickname': user.nickname,
        'role': user.role,
        'preferences': user.preferences,
        'mentor_verified': user.mentor_verified,
        'user_group': user_group,
        'photo_url': user.photo_url,
        'created_at': user.created_at,
        'updated_at': user.updated_at,
        'user_token': user.user_token,
        'uploaded_photo_url': user.uploaded_photo_url})
    return jsonify({"users": users_list}), 200


@app.route("/user", methods=['POST'])
def show_user():
    try:
        user_id = ObjectId(request.get_json()['user_id'])
        user = User.objects.get({'_id': user_id})
        user_group = None
        if user.user_group != None:
            user_group = CorporateGroup.objects.get({"_id": ObjectId(user.user_group)}).code
        return jsonify({
            'user_id': str(user._id),
            'name': user.name,
            'email': user.email,
            'mobile_no': user.mobile_no,
            'role': user.role,
            'nickname': user.nickname,
            'preferences': user.preferences,
            'mentor_verified': user.mentor_verified,
            'user_group': user_group,
            'photo_url': user.photo_url,
            'created_at': user.created_at,
            'updated_at': user.updated_at,
            'user_token': user.user_token,
            'uploaded_photo_url': user.uploaded_photo_url}), 200
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404


@app.route("/user/update", methods=['PATCH'])
def update_user():
    try:
        user_id = ObjectId(request.get_json()['user_id'])
        # validates if given user id is valid.
        User.objects.get({'_id': user_id})
        update_params = {}
        valid_params = ['name', 'mobile_no', 'role', 'nickname',
                        'photo_url', 'preferences', 'user_group', 
                        'mentor_verified', 'uploaded_photo_url', 
                        'background', 'linkedin', 'hours_per_day', 'certificates', 'courses']
        for key, value in request.get_json().items(): # validate update params
            if key in valid_params:
                update_params[key] = value
        User.from_document(update_params).full_clean(exclude=None)  # validate update params and raise exception if any
        user = User.objects.raw({'_id': user_id})
        update_params['updated_at'] = datetime.datetime.now().isoformat()
        if update_params['user_group'] != None:
            update_params['user_group'] = str(CorporateGroup.objects.get({'code': update_params['user_group']})._id)
        user.update({'$set': update_params})
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 200
    return jsonify({'message': 'User updated successfully.', 'error_status': False}), 202


@app.route("/user/delete", methods=['DELETE'])
def delete_user():
    try:
        user_id = ObjectId(request.get_json()['user_id'])
        User.objects.get({'_id': user_id}).delete()
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 200
    return jsonify({'message': 'User deleted from database.', 'error_status': False}), 202


# APIs for Session
@app.route("/session/create", methods=['POST'])
def create_session():
    create_params = {}
    try:
        valid_params = ['type', 'members', 'category', 'hours', 'description']
        for key, val in request.get_json().items():
            if key in valid_params:
                create_params[key] = val
        Session.from_document(create_params).full_clean(exclude=None)
        session = Session()
        session.save(force_insert=True)
        create_params['created_at'] = datetime.datetime.now().isoformat()
        Session.objects.raw({'_id': session._id}).update({'$set': create_params})
        # code.interact(local=dict(globals(), **locals()))
        Activity(
            user_id=create_params['members'][0],
            session_id=str(session._id),
            is_dynamic=False,
            content= ("You successfully requested for a new session for " + create_params['category'] + "."),
            created_at= datetime.datetime.now().isoformat()).save()
        socketio.emit('session', {'action': 'create', 'session_id': str(session._id)})
        
        time_in_secs = 30*60 # 30mins
        expiry_timer = Timer(time_in_secs, end_session_on_timer, (session._id, 'kill'))
        expiry_timer.start()
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 200
    return jsonify({'message': 'Successfully created session.', 'session_id': str(session._id), 'error_status': False}), 201

def end_session_on_timer(session_id, action):
    session_object_id = ObjectId(session_id)
    session = Session.objects.get({'_id': session_object_id })
    updater = Session.objects.raw({'_id': session_object_id })
    end_time = datetime.datetime.now()

    if action == 'end':
        seconds = (end_time - session.start_time).total_seconds()
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        active_duration = '{}:{}:{}'.format(hours, minutes, secs)
        updater.update({
            '$set': {
                "end_time": end_time.isoformat(), 
                "active_duration": active_duration,
                "updated_at": end_time.isoformat(), 
                'status': 'ended'
            }
        })
        Activity(
            user_id= session.members[0],
            session_id=str(session._id),
            is_dynamic= False,
            content= "Successfully Ended session for " + session.category + ".",
            created_at= end_time.isoformat()
        ).save()
    elif action == 'kill':
        updater.update({
            '$set': {
                "updated_at": end_time.isoformat(), 
                'status': 'lost'
            }
        })
        Activity(
            user_id= session.members[0],
            session_id=str(session._id),
            is_dynamic= False,
            content= "Your session request for " + session.category + " expired.",
            created_at= end_time.isoformat()
        ).save()

@app.route("/sessions/user", methods=['POST'])
def get_student_sessions():
    try:
        user_id = request.get_json()['user_id']
        User.objects.get({'_id': ObjectId(user_id)})
        sessions_list = []
        for session in Session.objects.raw({'status': {'$in': ["active", "ended"]},'members': {'$all':[user_id]}}):
            mentor = session.mentor
            mentor_details = {
                'name': mentor.name, 
                'nickname': mentor.nickname, 
                'user_id': str(mentor._id), 
                'email': mentor.email, 
                'uploaded_photo_url': mentor.uploaded_photo_url
            }
            student_id = session.members[0]
            student = User.objects.get({'_id': ObjectId(student_id)})
            student_details = {
                'name': student.name, 
                'nickname': student.nickname, 
                'user_id': str(student._id), 
                'email': student.email, 
                'uploaded_photo_url': student.uploaded_photo_url
                              }
            sessions_list.append({
                'session_id': str(session._id), 
                'type': session.type_, 
                'mentor': mentor_details, 
                'student': student_details,
                'members': session.members, 
                'start_time':session.start_time, 
                'status': session.status, 
                'active_duration': session.active_duration, 
                'end_time': session.end_time,
                'user_feedback': session.user_feedback,
                'mentor_feedback': session.mentor_feedback,
                "user_rating": session.user_rating,
                "mentor_rating": session.mentor_rating, 
                'category': session.category, 
                'created_at': session.created_at, 
                'updated_at': session.updated_at
                })
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404
    return jsonify({'sessions': sessions_list, 'error_status': False}), 200


@app.route("/sessions/mentor", methods=['POST'])
def get_mentor_sessions():
    try:
        user_id = request.get_json()['user_id']
        mentor = User.objects.get({'_id': ObjectId(user_id)})
        sessions_list = []
        for session in Session.objects.raw({'status': {'$in':["active", "ended"]}, 'mentor': mentor._id}):
            mentor = session.mentor
            mentor_details = {
                'name': mentor.name, 
                'nickname': mentor.nickname, 
                'user_id': str(mentor._id), 
                'email': mentor.email, 
                'uploaded_photo_url': mentor.uploaded_photo_url
            }
            student_id = session.members[0]
            student = User.objects.get({'_id': ObjectId(student_id)})
            student_details = {
                'name': student.name, 
                'nickname': student.nickname, 
                'user_id': str(student._id), 
                'email': student.email, 
                'uploaded_photo_url': student.uploaded_photo_url
            }
            sessions_list.append({
                'session_id': str(session._id),
                'type': session.type_,
                'mentor': mentor_details,
                'student': student_details,
                'members': session.members,
                'start_time': session.start_time,
                'status': session.status,
                'active_duration': session.active_duration,
                'end_time': session.end_time,
                'user_feedback': session.user_feedback,
                'mentor_feedback': session.mentor_feedback,
                "user_rating": session.user_rating,
                "mentor_rating": session.mentor_rating,
                'category': session.category,
                'created_at': session.created_at,
                'updated_at': session.updated_at
            })
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404
    return jsonify({'sessions': sessions_list, 'error_status': False}), 200


@app.route("/sessions/mentor/requests", methods=['POST'])
def get_requested_sessions():
    try:
        user_id = request.get_json()['user_id']
        mentor = User.objects.get({'_id': ObjectId(user_id)})
        preferences = mentor.preferences.copy()
        preferences.append('others')
        sessions_list = []
        for session in Session.objects.raw({'status': 'inactive', 'category': {'$in': preferences}}):
            # code.interact(local=dict(globals(), **locals()))
            student_id = session.members[0]
            student_obj = User.objects.get({'_id': ObjectId(student_id)})
            student_details = {
                'name': student_obj.nickname,
                'user_id': str(student_obj._id),
                'email': student_obj.email,
                'photo_url': student_obj.uploaded_photo_url
            }
            sessions_list.append({
                'session_id': str(session._id),
                'type': session.type_,
                'sender_details': student_details,
                'members': session.members,
                'start_time': session.start_time,
                'status': session.status,
                'active_duration': session.active_duration,
                'end_time': session.end_time,
                'user_feedback': session.user_feedback,
                'mentor_feedback': session.mentor_feedback,
                "user_rating": session.user_rating,
                "mentor_rating": session.mentor_rating,
                'category': session.category,
                'created_at': session.created_at,
                'updated_at': session.updated_at,
                'description': session.description
                })
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404
    return jsonify({'sessions': sessions_list, 'error_status': False}), 200


@app.route("/session", methods=['POST'])
def show_session():
    try:
        session_id = ObjectId(request.get_json()['session_id'])
        session = Session.objects.get({"_id": session_id})
        mentor = session.mentor
        studentId = session.members[0]
        student = User.objects.get({ "_id": ObjectId(studentId) })
        result = {
            'session_id': str(session._id),
            'type': session.type_,
            'members': session.members,
            'start_time': session.start_time,
            'status': session.status,
            'hours': session.hours,
            'active_duration': session.active_duration,
            'end_time': session.end_time,
            'user_feedback': session.user_feedback,
            'mentor_feedback': session.mentor_feedback,
            "user_rating": session.user_rating,
            "mentor_rating": session.mentor_rating,
            'category': session.category,
            'created_at': session.created_at,
            'updated_at': session.updated_at,
            'mentor': {
                'name': mentor.name,
                'nickname': mentor.nickname,
                'user_id': str(mentor._id),
                'email': mentor.email,
                'mobile_no': mentor.mobile_no,
                'certificates': mentor.certificates,
                'background': mentor.background,
                'courses': mentor.courses,
                'uploaded_photo_url': mentor.uploaded_photo_url
            } if mentor else {},
            'student': {
                'name': student.name,
                'nickname': student.nickname,
                'user_id': str(student._id),
                'mobile_no': student.mobile_no,
                'email': student.email,
                'uploaded_photo_url': student.uploaded_photo_url
            } if student else {}
        }
        return jsonify(result), 200
    except Exception as e:
        message = 'Session does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404


@app.route("/session/update", methods=['PATCH'])
def update_session_():
    update_params = {}
    try:
        valid_params = ['mentor_rating', 'user_rating', 'mentor_feedback', 'user_feedback']
        for key, val in request.get_json().items():
            if key in valid_params:
                update_params[key] = val
        session = Session.objects.get({'_id':ObjectId(request.get_json()['session_id'])})
        Session.from_document(update_params).full_clean(exclude=None)
        update_params['created_at'] = datetime.datetime.now().isoformat()
        Session.objects.raw({'_id': session._id}).update({'$set': update_params})
        socketio.emit('session', {'action': 'update', 'session_id': str(session._id)})
    except Exception as e:
        message = 'Session does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 422
    return jsonify({'message': 'Successfully updated session.', 'session_id': str(session._id), 'error_status': False}), 201

@app.route("/session/update/<string:action>", methods=['PATCH'])
def update_session(action=None):
    try:
        update_params = request.get_json()
        session_id = ObjectId(update_params['session_id'])
        # validates if given session id is valid.
        session_ = Session.objects.get({'_id': session_id})
        session = Session.objects.raw({'_id': session_id})
        socket_params = {'action': action, 'session_id': update_params['session_id'] }
        if action == "start" and session_.status == 'accepted':
            if update_params['student_id']:
                student = User.objects.get({'_id': ObjectId(update_params['student_id'])})
                if student.role != "student":
                    raise ValidationError("Given mentor id is incorrect, role of the user is not 'student'.")
            else:
                raise ValidationError("Student id is required to start a session.")
            session.update({'$set': {"start_time": datetime.datetime.now().isoformat(), "updated_at": datetime.datetime.now().isoformat(), 'status': 'active'}})
            Activity(user_id= session_.members[0], session_id=str(session_._id), is_dynamic= False, content= "You successfully started a session for " + session_.category + ".", created_at= datetime.datetime.now().isoformat()).save()
            socket_params["mentor_id"] = str(session_.mentor._id)

            expiry_timer.cancel()
            time_in_secs = session_.hours*60*60 
            expiry_timer = Timer(time_in_secs, end_session_on_timer, (session_._id, 'end'))
            expiry_timer.start()
        elif action == "end" and session_.status == 'active':
            end_time = datetime.datetime.now()
            seconds = (end_time - session_.start_time).total_seconds()
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            active_duration = '{}:{}:{}'.format(hours, minutes, secs)
            session.update({'$set': {"end_time": end_time.isoformat(), "active_duration": active_duration,
                                     "updated_at": datetime.datetime.now().isoformat(), 'status': 'ended'}})
            Activity(user_id= session_.members[0], session_id=str(session_._id), is_dynamic= False, content= "Successfully Ended session for " + session_.category + ".", created_at= datetime.datetime.now().isoformat()).save()
            expiry_timer.cancel()
        elif action == "accept" and session_.status == 'inactive':
            if update_params['mentor_id']:
                mentor = User.objects.get({'_id': ObjectId(update_params['mentor_id'])})
                if mentor.role != "mentor":
                    raise ValidationError("Given mentor id is incorrect, role of the user is not 'mentor'.")
            else:
                raise ValidationError("Mentor id is required to accept a session.")
            session.update({'$set': {"updated_at": datetime.datetime.now().isoformat(), 'status': 'accepted', "mentor": mentor._id}})
            Activity(user_id= session_.members[0], session_id=str(session_._id), is_dynamic= True, content= (mentor.name + " accepted your session for " + session_.category + "."), created_at= datetime.datetime.now().isoformat()).save()
        elif action == "kill" and session_.status == 'inactive':
            session.update({'$set': {"updated_at": datetime.datetime.now().isoformat(), 'status': 'lost'}})
        else:
            raise ValidationError("Presently the session is " + session_.status)

        socketio.emit('session', socket_params)

    except Exception as e:
        message = 'Session does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 200
    return jsonify({'message': 'Successfully updated session.', 'error_status': False}), 202

# APIs for Message
@app.route("/message/create", methods=['POST'])
def create_message():
    try:
        create_params = request.get_json()
        create_params['created_at'] = datetime.datetime.now().isoformat()
        message = Message(session=create_params['session_id'], sender=create_params['sender_id'],
                          content=create_params['content'], type_=create_params['type'], created_at=create_params['created_at'])
        message.save()
        socketio.emit('chat-' + create_params['session_id'], create_params)
    except Exception as e:
        return jsonify({"error": str(e), 'error_status': True}), 200
    return jsonify({'message': 'Successfully created a message.', 'error_status': False}), 201

@app.route("/message/typing", methods=['POST'])
def typing_message():
    params = request.get_json()
    session_id = params['session_id']
    sender_id = params['sender_id']
    is_typing = params['is_typing']
    socketio.emit('chat-' + session_id, { 'type': 'typing', 'sender_id': sender_id, 'is_typing': is_typing })
    return jsonify({ 'message': 'Typing status updated'}), 200


@app.route("/messages", methods=['POST'])
def get_messages():
    try:
        session_id = ObjectId(request.get_json()['session_id'])
        session = Session.objects.get({'_id': session_id})
        result = []
        messages = Message.objects.raw({'session': session_id})
        for message in messages:
            user = message.sender
            sender_details = {"user_id": str(
                user._id), "name": user.name, "email": user.email, "role": user.role}
            result.append({"message_id": str(message._id), "session_id": str(message.session._id), "sender": sender_details,
                           "content": message.content, "type": message.type_, "created_at": message.created_at})
    except Exception as e:
        message = 'Session does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404
    return jsonify({'messages': result, 'error_status': False}), 200

# APIs for Corporate Group
@app.route("/corporate/create", methods=['POST'])
def create_corporate_group():
    try:
        params = request.get_json()
        CorporateGroup(code=params['code'], categories=params['categories']).save(full_clean=True)
    except Exception as e:
        return jsonify({'error': str(e), 'error_status': True}), 404
    return jsonify({'message': "Successfully created group.", "error_status": False}), 201


@app.route("/user/corporate", methods=["POST"])
def get_corporate_for_user():
    try:
        user = User.objects.get({'_id': ObjectId(request.get_json()['user_id'])})
        group = CorporateGroup.objects.get({"_id": ObjectId(user.user_group)})
        return jsonify({"code": group.code, "categories": group.categories, "id": str(group._id)}), 200
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404

@app.route("/corporates", methods=["GET"])
def get_all_sessions():
    groups = CorporateGroup.objects.all()
    data = []
    for group in groups:
        data.append({"code": group.code, "categories": group.categories, "id": str(group._id)})
    return jsonify({"corporates": data}), 200


@app.route("/activity/create", methods=['POST'])
def create_activity():
    try:
        create_params = {}
        valid_params = ['is_dynamic', 'user_id', 'content']
        for key, val in request.get_json().items():
            if key in valid_params:
                create_params[key] = val
        activity = Activity().save()
        Activity.from_document(create_params).full_clean(exclude=None)
        create_params['created_at'] = datetime.datetime.now().isoformat()
        Activity.objects.raw({'_id':activity._id}).update({'$set': create_params})
    except Exception as e:
        activity.delete()
        return jsonify({'error': str(e), 'error_status': True}), 422
    return jsonify({'activity_id': str(activity._id),'message': "Successfully created activity", 'error_status': False}), 201

@app.route("/activity/update", methods=['POST'])
def update_activity():
    try:
        activity = Activity.objects.raw({'_id': ObjectId(request.get_json()['activity_id'])})
        update_params = {}
        valid_params = ['content','is_dynamic']
        for key, val in request.get_json().items():
            if key in valid_params:
                update_params[key] = val
        Activity.from_document(update_params).full_clean(exclude=None)
        update_params['updated_at'] = datetime.datetime.now().isoformat()
        activity.update({'$set': update_params})
    except Exception as e:
        return jsonify({'error': str(e), 'error_status': True}), 422
    return jsonify({'message': "Successfully updated activity", 'error_status': False}), 201

@app.route("/activity", methods=['POST'])
def get_activity():
    try:
        user_id = request.get_json()['user_id']
        activities = Activity.objects.raw({'user_id': user_id})
        user_activities = []
        for activity in activities:
            user_activities.append({
                'activity_id': str(activity._id), 
                'session_id': activity.session_id, 
                'is_dynamic': activity.is_dynamic, 
                'content': activity.content, 
                'user_id': activity.user_id,
                'created_at': activity.created_at
            })
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404
    return jsonify({"activities": user_activities}), 200


if __name__ == '__main__':
    socketio.run(app)
    # app.run(port=3000, debug=True, host='localhost')