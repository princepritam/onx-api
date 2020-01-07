# APIs for Connection
import datetime, code, dateutil.parser
from flask import Blueprint, request, jsonify
from bson import ObjectId, errors
from pymongo.errors import DuplicateKeyError
from app.models.session import *
from app.models.connection import *
from app.models.activity import *
from threading import Timer
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

            connection_list.append({
                'connection_id': connection._id,
                'mentor_details': mentor_details,
                'category': connection.category,
                'status': connection.status,
                'scheduled_time': connection.scheduled_time,
            })
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
            connection_list.append({
                'connection_id': connection._id,
                'student_details': student_details,
                'category': connection.category,
                'status': connection.status,
                'scheduled_time': connection.scheduled_time,
            })
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404
    return jsonify({'connections': connection_list, 'error_status': False}), 200