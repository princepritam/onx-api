# APIs for Session
import datetime
from flask import Blueprint, request, jsonify
from bson import ObjectId, errors
from pymongo.errors import DuplicateKeyError
from app.models.session import *
from app.models.activity import *
from threading import Timer
from . import app, socketio, emit

main = Blueprint('session', __name__)

expiry_timer = None

@main.route("/session/create", methods=['POST'])
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

@main.route("/sessions/user", methods=['POST'])
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


@main.route("/sessions/mentor", methods=['POST'])
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


@main.route("/sessions/mentor/requests", methods=['POST'])
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


@main.route("/session", methods=['POST'])
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


@main.route("/session/update", methods=['PATCH'])
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

@main.route("/session/update/<string:action>", methods=['PATCH'])
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