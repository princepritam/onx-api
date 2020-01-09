# APIs for Session
import datetime, code, dateutil.parser
from flask import Blueprint, request, jsonify
from bson import ObjectId, errors
from pymongo.errors import DuplicateKeyError
from celery.task.control import revoke
from celery.result import AsyncResult
import redis
from app.models.session import *
from app.models.activity import *
<<<<<<< Updated upstream
from app.models.connection import *
from threading import Timer
from . import app, socketio, emit, celery
=======
from . import app, socketio, emit, celery_client
>>>>>>> Stashed changes

main = Blueprint('session', __name__)

redis_conn_local = redis.Redis(host='localhost', port=6379, db=0)
redis_conn_deploy = redis.Redis(host='barb.redistogo.com',port=10037, db=0, password='45efe1ab922687bd6d3f31101e657317')

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
        kill_session_task = kill_session.apply_async([str(session._id)], countdown=60)
        kill_session_task.revoke(terminate=True)
        # code.interact(local=dict(globals(), **locals()))
        # AsyncResult(kill_session_task.id).revoke(terminate=True, signal='SIGKILL')
        redis_conn_local.set(str(session._id), kill_session_task.id.encode('utf=8'))
        Activity(
            user_id=create_params['members'][0],
            session_id=str(session._id),
            is_dynamic=False,
            content= ("You successfully requested for a new session for " + create_params['category'] + "."),
            created_at= datetime.datetime.now().isoformat()).save()
        socketio.emit('session', {'action': 'create', 'session_id': str(session._id)})
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 200
    return jsonify({'message': 'Successfully created session.', 'session_id': str(session._id), 'error_status': False}), 201


@main.route("/session/schedule", methods=['POST'])
def schedule_session():
    create_params = {}
    try:
        params = request.get_json()
        session_id = params['session_id']
        scheduled_time = params['scheduled_time']
        session_obj = Session.objects.get({'_id': ObjectId(session_id) })
        current_time = datetime.datetime.now().isoformat()
        new_session_document = {
            'type_': session_obj.type_,
            'members': session_obj.members,
            'category': session_obj.category,
            'created_at': current_time,
            'status': 'scheduled_inactive',
            'scheduled_time': scheduled_time,
            'mentor': session_obj.mentor._id
        }
        Session.from_document(new_session_document).full_clean(exclude=None)
        session = Session()
        session.save(force_insert=True)
        Session.objects.raw({'_id': session._id}).update({'$set': new_session_document})
        # code.interact(local=dict(globals(), **locals()))
        Activity(
            user_id= session_obj.members[0],
            session_id=str(session._id),
            is_dynamic=True,
            content=("You successfully requested for a new session for " + session_obj.category + "with" + session_obj.mentor.name + "."),
            created_at= current_time
        ).save()

        socketio.emit('session', {'action': 'create', 'session_id': str(session._id)})
        
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 200
    return jsonify({'message': 'Successfully created session.', 'session_id': str(session._id), 'error_status': False}), 201

@celery_client.task
def schedule_session(session):
    session.update({'$set': {'status': 'accepted', 'updated_at': datetime.datetime.now().isoformat}})
    Activity(
        user_id= session.members[0],
        session_id=str(session._id),
        is_dynamic= True,
        content= "Please start your session for " + session.category + ".",
        created_at= datetime.datetime.now().isoformat()).save()
    socket_params["student_id"] = session.members[0]
    socket_params["mentor_id"] = str(session.mentor._id)


@celery_client.task
def end_session():
    update_session("end")


@celery_client.task
def kill_session(session_id):
    Session.objects.raw({'_id':ObjectId(session_id)}).update({'$set': {'updated_at': datetime.datetime.now().isoformat(), 'status': 'lost'}})
    return str(session_id)


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

@main.route("/sessions", methods=['GET'])
def get_all_sessions():
    try:
        sessions = Session.objects.all()
        sessions_list = []
        for session in sessions:
            mentor = session.mentor
            mentor_details = {
                'name': mentor.name, 
                'nickname': mentor.nickname, 
                'user_id': str(mentor._id), 
                'email': mentor.email, 
                'uploaded_photo_url': mentor.uploaded_photo_url
            } if mentor else {}
            student_id = session.members[0]
            student = User.objects.get({'_id': ObjectId(student_id)})
            student_details = {
                'name': student.name, 
                'nickname': student.nickname, 
                'user_id': str(student._id), 
                'email': student.email, 
                'uploaded_photo_url': student.uploaded_photo_url
            } if student else {}
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
        return jsonify({'error': str(e), 'error_status': True}), 404
    return jsonify({'sessions': sessions_list, 'error_status': False}), 200

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
            } if mentor else {}
            student_id = session.members[0]
            student = User.objects.get({'_id': ObjectId(student_id)})
            student_details = {
                'name': student.name, 
                'nickname': student.nickname, 
                'user_id': str(student._id), 
                'email': student.email, 
                'uploaded_photo_url': student.uploaded_photo_url
            } if student else {}
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
        for session in Session.objects.raw({'status': {'$in':["active", "ended", "scheduled_inactive"]}, 'mentor': mentor._id}):
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
        # code.interact(local=dict(globals(), **locals()))
        for session in Session.objects.raw({'$or': [{'status': {'$in':['inactive']}, 'category': {'$in': preferences}},
                                                    {'status': {'$in':['scheduled_inactive']}, 'mentor': mentor._id}]}):
            student_id = session.members[0]
            student_obj = User.objects.get({'_id': ObjectId(student_id)})
            student_details = {
                'nickname': student_obj.nickname,
                'user_id': str(student_obj._id),
                'email': student_obj.email,
                'uploaded_photo_url': student_obj.uploaded_photo_url
            }
            sessions_list.append({
                'session_id': str(session._id),
                'type': session.type_,
                'student_details': student_details,
                'members': session.members,
                'start_time': session.start_time,
                'status': session.status,
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
                'uploaded_photo_url': mentor.uploaded_photo_url,
                'certificates': mentor.certificates,
                'background': mentor.background,
                'courses': mentor.courses,
                'linkedin': mentor.linkedin,
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
        update_params['updated_at'] = datetime.datetime.now().isoformat()
        Session.objects.raw({'_id': session._id}).update({'$set': update_params})
        socketio.emit('session', {'action': 'update', 'session_id': str(session._id)})
    except Exception as e:
        message = 'Session does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 422
    return jsonify({'message': 'Successfully updated session.', 'session_id': str(session._id), 'error_status': False}), 201

def getConnection(session_obj, mentor_id):
    student_id = session_obj.members[0]
    connection = Connection.objects.get({ 'mentor': ObjectId(mentor_id), 'members':  { '$all':[student_id] } })
    return connection 

@main.route("/session/update/<string:action>", methods=['PATCH'])
def update_session(action=None):
    try:
        update_params = request.get_json()
        session_id = ObjectId(update_params['session_id'])
        session_ = Session.objects.get({'_id': session_id})
        session = Session.objects.raw({'_id': session_id})
        socket_params = {'action': action, 'session_id': update_params['session_id'] }
        
        if action == "start" and session_.status in ['accepted']:
            kill_accepted_task_id = redis_conn_local.get(update_params['session_id']).decode('utf-8')
            AsyncResult(kill_accepted_task_id).revoke(terminate=True)
            if update_params['student_id']:
                student = User.objects.get({'_id': ObjectId(update_params['student_id'])})
                if student.role != "student":
                    raise ValidationError("Given mentor id is incorrect, role of the user is not 'student'.")
            else:
                raise ValidationError("Student id is required to start a session.")
            student_updater = User.objects.raw({'_id': ObjectId(update_params['student_id'])})
            mentor_updater = User.objects.raw({'_id': session_.mentor._id})
            student_sessions = student.sessions + 1
            mentor_sessions = session_.mentor.sessions + 1
            student_updater.update({'$set':{"sessions": student_sessions}})
            mentor_updater.update({'$set':{"sessions": mentor_sessions}})

            Connection.objects.raw({ '_id': session_.connection_id._id }).update({'$set': {
                "updated_at": datetime.datetime.now().isoformat(),
                'status': 'active'
            }})

            session.update({'$set': {
                "start_time": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                'status': 'active'
            }})
            Activity(
                user_id= session_.members[0],
                session_id=str(session_._id),
                is_dynamic= False,
                content= "You successfully started a session for " + session_.category + ".",
                created_at= datetime.datetime.now().isoformat()).save()
            socket_params["mentor_id"] = str(session_.mentor._id)

        elif action == "end" and session_.status == 'active':
            end_time = datetime.datetime.now()
            seconds = (end_time - session_.start_time).total_seconds()
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            active_duration = '{}:{}:{}'.format(hours, minutes, secs)

            # expiry_timer = session_expiry_timer_map[update_params['session_id']]
            # expiry_timer.cancel()

            Connection.objects.raw({ '_id': session_.connection_id._id }).update({'$set': {
                "updated_at": datetime.datetime.now().isoformat(),
                'status': 'ended'
            }})

            session.update({'$set': {"end_time": end_time.isoformat(), "active_duration": active_duration,
                                     "updated_at": datetime.datetime.now().isoformat(), 'status': 'ended'}})
            Activity(user_id= session_.members[0], session_id=str(session_._id), is_dynamic= False, content= "Successfully Ended session for " + session_.category + ".", created_at= datetime.datetime.now().isoformat()).save()
            student_id = session_.members[0]
            socket_params["student_id"] = str(student_id)
            socket_params["mentor_id"] = str(session_.mentor._id)

        elif action == "accept" and session_.status == 'inactive':
            mentor_id = update_params['mentor_id']
            if mentor_id:
                mentor = User.objects.get({'_id': ObjectId(mentor_id)})
                if mentor.role != "mentor":
                    raise ValidationError("Given mentor id is incorrect, role of the user is not 'mentor'.")
            else:
                raise ValidationError("Mentor id is required to accept a session.")
<<<<<<< Updated upstream
            connection = getConnection(session_, mentor_id)
            connection_id = connection._id if connection else None
            if (connection_id):
                sessions = connection.sessions
                sessions.append(str(session_._id))
                Connection.objects.raw({ '_id': connection_id }).update({'$set': {
                    'sessions': sessions,
                    'status': 'accepted',
                }})
            else:
                sessions=[str(session_._id)]
                conn = Connection()
                conn.save()
                Connection.objects.raw({ '_id': conn._id}).update({'$set': {
                    'sessions': sessions,
                    'status': 'accepted',
                    'mentor': ObjectId(mentor_id),
                    'members': session_.members,
                    'category': session_.category
                }})
                connection_id = conn._id
            session.update({'$set': { 
                'connection_id': connection_id, 
                "updated_at": datetime.datetime.now().isoformat(), 
                'status': 'accepted', 
                "mentor": mentor._id
            }})
            Activity(user_id= session_.members[0], session_id=str(session_._id), is_dynamic= True, content= (mentor.nickname + " accepted your session for " + session_.category + "."), created_at= datetime.datetime.now().isoformat()).save()

=======
            session.update({'$set': {"updated_at": datetime.datetime.now().isoformat(), 'status': 'accepted', "mentor": mentor._id}})
            kill_session_task_id = redis_conn_local.get(update_params['session_id']).decode('utf-8')
            terminate_task(kill_session_task_id)
            kill_acepted_session = kill_session.apply_async([update_params['session_id']], countdown=20)
            redis_conn_local.set(update_params['session_id'], kill_acepted_session.id.encode('utf-8'))
            Activity(user_id= session_.members[0], session_id=str(session_._id), is_dynamic= True, content= (mentor.nickname + " accepted your session for " + session_.category + "."), created_at= datetime.datetime.now().isoformat()).save()
>>>>>>> Stashed changes
            student_id = session_.members[0]
            socket_params["student_id"] = str(student_id)

        elif action == "accept" and session_.status == 'scheduled_inactive':
            session.update({'$set': {"updated_at": datetime.datetime.now().isoformat(), 'status': 'scheduled_active'}})
            scheduled_time = dateutil.parser.parse(session.scheduled_time)
            current_time = datetime.datetime.now()
            countdown_seconds = (scheduled_time - current_time).total_seconds()
            schedule_session = schedule_session(session).apply_async(countdown=countdown_seconds)
            Activity(
                user_id= session_.members[0],
                session_id=str(session_._id),
                is_dynamic= True,
                content= (mentor.nickname + " accepted your session for " + session_.category + ", and has been scheduled as per your request."),
                created_at= datetime.datetime.now().isoformat()).save()        
            student_id = session_.members[0]
            socket_params["student_id"] = str(student_id)

        elif action == "kill" and session_.status == 'inactive':
            session.update({'$set': {"updated_at": datetime.datetime.now().isoformat(), 'status': 'lost'}})

        elif action == "schedule" and session_.status == 'scheduled_inactive':
            session.update({'$set': {"updated_at": datetime.datetime.now().isoformat(), 'status': 'scheduled_active'}})

        else:
            raise ValidationError("Presently the session is " + session_.status)
        socketio.emit('session', socket_params)

    except Exception as e:
        message = 'Session does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 200
    return jsonify({'message': 'Successfully updated session.', 'error_status': False}), 202

@main.route('/terminate', methods=['POST'])
def terminate_task():
    task_id = request.get_json()['task_id']
    task = AsyncResult(task_id)
    task.revoke(terminate=True)