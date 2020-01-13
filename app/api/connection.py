# APIs for Connection
import datetime, code, dateutil.parser
from flask import Blueprint, request, jsonify
from bson import ObjectId, errors
from pymongo.errors import DuplicateKeyError
from app.models.session import *
from app.models.connection import *
from app.models.activity import *
from app.models.message import *
from functools import reduce
from . import app, socketio, emit, celery

main = Blueprint('connection', __name__)

@main.route("/connection/create", methods=['POST'])
def create_connection():
    try:
        params = request.get_json()
        sessions = params['sessions']
        session_id = sessions[0]
        session_obj = Session.objects.get({ '_id':ObjectId(session_id) })
        create_params = {
            'mentor': session_obj.mentor._id,
            'members': session_obj.members,
            'category': session_obj.category,
            'sessions': sessions,
            'status': 'accepted',
            'created_at': datetime.datetime.now().isoformat()
        }

        # Connection.from_document(create_params).full_clean(exclude=None)
        conn = Connection()
        conn.save()
        Connection.objects.raw({'_id': conn._id}).update({'$set': create_params})
    except Exception as e:
        message = 'Connection does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 200
    return jsonify({'message': 'Successfully created connection.', 'session_id': str(conn._id), 'error_status': False}), 201


@main.route("/connection/continue", methods=['POST'])
def create_connection_session():
    create_params = {}
    try:
        connection_id = ObjectId(request.get_json()['connection_id'])
        connection = Connection.objects.get({'_id': connection_id})
        # code.interact(local=dict(globals(), **locals()))
        mentor = connection.mentor
        members = connection.members
        category = connection.category
        session_document = {
            "mentor": mentor._id,
            "members": members,
            "category": category,
            "status": "inactive",
            "type": "single",
            "created_at": datetime.datetime.now().isoformat()
        }
        Session.from_document(session_document).full_clean(exclude=None)
        session = Session()
        session.save(force_insert=True)
        Session.objects.raw({'_id': session._id}).update({'$set': session_document})

    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 200
    return jsonify({'message': 'Successfully created session.', 'session_id': str(session._id), 'error_status': False}), 201


@main.route("/connection/update", methods=['PATCH'])
def update_connection():
    update_params = {}
    try:
        valid_params = ['sessions', 'status', 'scheduled_time']
        for key, val in request.get_json().items():
            if key in valid_params:
                update_params[key] = val
        conn = Connection.objects.get({'_id':ObjectId(request.get_json()['connection_id'])})
        Connection.from_document(update_params).full_clean(exclude=None)
        update_params['updated_at'] = datetime.datetime.now().isoformat()
        Connection.objects.raw({'_id': conn._id}).update({'$set': update_params})
    except Exception as e:
        message = 'Session does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 422
    return jsonify({'message': 'Successfully updated connection.', 'error_status': False}), 201

@main.route("/connections", methods=['GET'])
def get_all_connections():
    try:
        connections = Connection.objects.all()
        connection_list = []
        for conn in connections:
            mentor = conn.mentor
            mentor_details = {
                'name': mentor.name, 
                'nickname': mentor.nickname, 
                'user_id': str(mentor._id), 
                'email': mentor.email, 
                'uploaded_photo_url': mentor.uploaded_photo_url
            } if mentor else {}
            student_id = conn.members[0]
            student = User.objects.get({'_id': ObjectId(student_id)})
            student_details = {
                'name': student.name, 
                'nickname': student.nickname, 
                'user_id': str(student._id), 
                'email': student.email, 
                'uploaded_photo_url': student.uploaded_photo_url
            } if student else {}
            connection_list.append({
                'connection_id': str(conn._id),
                'mentor_details': mentor_details,
                'student_details': student_details,
                'session_count': len(conn.sessions),
                'category': conn.category,
                'status': conn.status,
                'members': conn.members,
                'mentor': str(conn.mentor._id),
            })
    except Exception as e:
        return jsonify({'error': str(e), 'error_status': True}), 404
    return jsonify({'connections': connection_list, 'error_status': False}), 200

@main.route("/connections/user", methods=['POST'])
def get_user_connections():
    try:
        user_id = request.get_json()['user_id']
        User.objects.get({'_id': ObjectId(user_id)})
        connection_list = []
        for connection in Connection.objects.raw({'status': {'$in': ["active", "ended", 'accepted', 'scheduled']},'members': {'$all':[user_id]}}):
            mentor = connection.mentor
            mentor_details = {
                'name': mentor.name, 
                'nickname': mentor.nickname, 
                'user_id': str(mentor._id), 
                'email': mentor.email, 
                'uploaded_photo_url': mentor.uploaded_photo_url
            } if mentor else {}

            conn_obj = {
                'connection_id': str(connection._id),
                'mentor': mentor_details,
                'category': connection.category,
                'status': connection.status,
                'created_at': connection.created_at.isoformat(),
                'updated_at': connection.updated_at.isoformat(),
            }
            if connection.scheduled_time != None:
                conn_obj["scheduled_time"] = connection.scheduled_time.isoformat()
            connection_list.append(conn_obj)
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404
    return jsonify({'connections': connection_list, 'error_status': False}), 200 

@main.route("/connections/mentor", methods=['POST'])
def get_mentor_connections():
    try:
        user_id = request.get_json()['user_id']
        User.objects.get({'_id': ObjectId(user_id)})
        connection_list = []
        connections = Connection.objects.raw({'status': {'$in': ["active", "ended", 'accepted', 'scheduled']}, 'mentor': ObjectId(user_id) })
        for connection in connections:
            student_id = connection.members[0]
            student = User.objects.get({'_id': ObjectId(student_id)})
            student_details = {
                'name': student.name, 
                'nickname': student.nickname, 
                'user_id': str(student._id), 
                'email': student.email, 
                'uploaded_photo_url': student.uploaded_photo_url
            } if student else {}
            conn_obj = {
                'connection_id': str(connection._id),
                'student': student_details,
                'category': connection.category,
                'status': connection.status,
                'created_at': connection.created_at.isoformat(),
                'updated_at': connection.updated_at.isoformat(),
            }
            if connection.scheduled_time != None:
                conn_obj["scheduled_time"] = connection.scheduled_time.isoformat()
            connection_list.append(conn_obj)
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404
    return jsonify({'connections': connection_list, 'error_status': False}), 200

def fetch_messages(session_id):
    result = []
    messages = Message.objects.raw({'session': ObjectId(session_id)})
    for message in messages:
        user = message.sender
        sender_details = {
            "user_id": str(user._id), 
            "nickname": user.nickname, 
            "email": user.email, 
            "role": user.role
        }
        result.append({
            "message_id": str(message._id), 
            "session_id": str(message.session._id), 
            "sender": sender_details,
            "content": message.content, 
            "type": message.type_, 
            "created_at": message.created_at.isoformat()
        })
    return result

def fetch_sessions(output, session_id):
    session_obj = Session.objects.get({'_id': ObjectId(session_id)})
    messages = fetch_messages(session_id)
    session_map = {
        'session_id': session_id,
        'session_status': session_obj.status,
        'created_at': session_obj.created_at.isoformat(),
        'updated_at': session_obj.updated_at.isoformat(),
        'start_time': session_obj.start_time,
        'end_time': session_obj.end_time,
        'messages': messages,
        'user_rating': session_obj.user_rating,
        'user_feedback': session_obj.user_feedback,
        'mentor_rating': session_obj.mentor_rating,
        'mentor_feedback': session_obj.mentor_feedback
    }
    # code.interact(local=dict(globals(), **locals()))
    new_map = { session_id: session_map }
    return dict(**output, **new_map)

@main.route("/connection", methods=['POST'])
def get__connection():
    try:
        connection_id = request.get_json()['connection_id']
        connection = Connection.objects.get({'_id': ObjectId(connection_id)})
        sessions = connection.sessions
        # code.interact(local=dict(globals(), **locals()))
        session_detail_map = reduce(fetch_sessions, sessions, {})
        student_id = connection.members[0]
        mentor_obj = connection.mentor
        student_obj = User.objects.get({'_id': ObjectId(student_id)})
        mentor = {
            "user_id": str(mentor_obj._id), 
            "nickname": mentor_obj.nickname, 
            "uploaded_photo_url": mentor_obj.uploaded_photo_url, 
            "email": mentor_obj.email, 
            "role": mentor_obj.role
        }
        student = {
            "user_id": str(student_obj._id), 
            "uploaded_photo_url": student_obj.uploaded_photo_url, 
            "nickname": student_obj.nickname, 
            "email": student_obj.email, 
            "role": student_obj.role
        }
        conn_obj = {
            'connection_id': connection_id,
            'status': connection.status,
            'sessions': session_detail_map,
            'student': student,
            'mentor': mentor,
            'category': connection.category
        }
        if connection.scheduled_time != None:
            conn_obj["scheduled_time"] = connection.scheduled_time.isoformat()
    except Exception as e:
        message = 'Connection does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404
    return jsonify({'connection': conn_obj, 'error_status': False}), 200


@main.route("/connection/schedule", methods=['POST'])
def schedule_session():
    try:
        params = request.get_json()
        connection_id = params['connection_id']
        scheduled_time = params['scheduled_time']
        scheduled_time = dateutil.parser.parse(scheduled_time)
        if scheduled_time <= utc_iso_format(datetime.datetime.now()):
            raise ValidationError("Scheduled datetime cannot be prior to current datetime. ")
        current_time = datetime.datetime.now().isoformat()
        conn = Connection.objects.get({'_id': ObjectId(connection_id) })
        new_session_document = {
            'type_': 'single',
            'members': conn.members,
            'category': conn.category,
            'created_at': current_time,
            'status': 'scheduled',
            'mentor': str(conn.mentor._id),
            'connection_id': ObjectId(connection_id)
        }
        Session.from_document(new_session_document).full_clean(exclude=None)
        session = Session()
        session.save(force_insert=True)
        Session.objects.raw({'_id': session._id}).update({'$set': new_session_document})

        sessions = conn.sessions
        sessions.append(str(session._id))
        Connection.objects.raw({'_id': ObjectId(connection_id)}).update({'$set':{
            "status": 'scheduled',
            'scheduled_time': scheduled_time.isoformat(),
            "sessions": sessions
        }})
        current_time = utc_iso_format(datetime.datetime.now())
        countdown_seconds = (scheduled_time - current_time).total_seconds()
        schedule_session = schedule_session_job.apply_async([session], countdown=countdown_seconds)
        notifier_countdown_seconds = countdown_seconds - 7200
        # code.interact(local=dict(globals(), **locals()))
        notify_mentor = create_notification.apply_async([session.members[0], session], countdown=notifier_countdown_seconds)
        notify_student = create_notification.apply_async([str(session.mentor._id), session], countdown=notifier_countdown_seconds)
        Activity(
            user_id= session_obj.members[0],
            session_id=str(session._id),
            is_dynamic=False,
            content=("You successfully scheduled a new session for " + session_obj.category + "."),
            created_at= current_time
        ).save()

        socketio.emit('session', {'action': 'create', 'session_id': str(session._id)})
        
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 200
    return jsonify({'message': 'Successfully created session.', 'session_id': str(session._id), 'error_status': False}), 201

@celery.task
def schedule_session_job(session):
    session.update({'$set': {'status': 'accepted', 'updated_at': datetime.datetime.now().isoformat()}})     
    Connection.objects.raw({'_id': ObjectId(session.connection_id)}).update({'$set':{"status": 'accepted'}})

@celery.task
def create_notification(user_id,session):
    Activity(
        user_id= user_id,
        session_id=str(session._id),
        is_dynamic=False,
        content=("Your session will start in 2 hours for " + session.category + "."),
        created_at= datetime.datetime.now().isoformat()
    ).save()
def utc_iso_format(dt):
    try:
        utc = dt + dt.utcoffset()
    except TypeError as e:
        utc = dt
    isostring = datetime.datetime.strftime(utc, '%Y-%m-%dT%H:%M:%S.{0}Z')
    return dateutil.parser.parse(isostring.format(int(round(utc.microsecond/1000.0))))