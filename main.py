#!flask/bin/python
# Python standard libraries
import code, os, json, datetime, time

from flask import Flask, redirect, url_for, request, jsonify
from bson import ObjectId, errors
from pymodm.connection import connect
from pymongo.errors import DuplicateKeyError
from flask_socketio import SocketIO, emit
from app.models.models import *

deploy = "mongodb://testuser:qwerty123@ds241258.mlab.com:41258/heroku_mjkv6v40"
# deploy="mongodb://heroku_mjkv6v40:osce9dakl9glgd4750cuovm8h1@ds241258.mlab.com:41258/heroku_mjkv6v40"
local = "mongodb://localhost:27017/onx"

connect(deploy, alias="onx-app", retryWrites=False)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'unxunxunx'
socketio = SocketIO(app, cors_allowed_origins="*")

# Health check
@app.route("/ping", methods=['GET'])
def home():
	return 'hello'


# APIs for User
@app.route("/user/create", methods=['POST'])
def create_user():
	params = request.get_json()
	try:
		user = User(email=params['email'], name=params['name'], role=params['role'], user_token=params['user_token'],
					 created_at=datetime.datetime.now().isoformat(), updated_at=datetime.datetime.now().isoformat(), photo_url=params['photo_url'])
		user.save(force_insert=True)
	except Exception as e:
		if str(e) == 'User with this email already exist':
			user = User.objects.get({'email':params['email']})
			return jsonify({'message': str(e), 'error_status': False, 'user_id': str(user._id), 'role': user.role, 'previously_logged_in': True}), 200
		return jsonify({'error': str(e), 'error_status': True}), 200
	return jsonify({'message': 'Successfully created user.','user_id': str(user._id), 'error_status': False}), 201

@app.route("/users", methods=['POST'])
def get_all_users():
	users_list = []
	for user in User.objects.all():
		users_list.append({'user_id': str(user._id), 'name':user.name, 'email':user.email,
								'mobile_no':user.mobile_no, 'nickname': user.nickname, 'role':user.role, 'preferences':user.preferences, 'user_group':user.user_group, 'photo_url':user.photo_url, 'created_at':user.created_at, 'updated_at':user.updated_at})
	return jsonify({"Users": users_list}), 200

@app.route("/user", methods=['POST'])
def show_user():
	try:
		user_id = ObjectId(request.get_json()['user_id'])
		user = User.objects.get({'_id': user_id})
		return jsonify({'user_id': str(user._id), 'name':user.name, 'email':user.email,
						'mobile_no':user.mobile_no, 'role':user.role, 'nickname': user.nickname, 'preferences':user.preferences, 'user_group':user.user_group, 'photo_url':user.photo_url, 'created_at':user.created_at, 'updated_at':user.updated_at, 'user_token':user.user_token}), 200
	except Exception as e :
		message = 'User does not exists.' if str(e) == '' else str(e)
		return jsonify({'error': message, 'error_status': True}), 404


@app.route("/user/update", methods=['PATCH'])
def update_user():
	try:
		user_id = ObjectId(request.get_json()['user_id'])
		User.objects.get({'_id': user_id}) #validates if given user id is valid.
		update_params = {}
		valid_params = ['name', 'mobile_no', 'role', 'nickname', 'photo_url', 'preferences', 'user_group']
		for key, value in request.get_json().items():
			if key in valid_params:
				update_params[key] = value
		user = User.objects.raw({'_id': user_id})
		user_valid = User.from_document(update_params) #validate update params
		user_valid.full_clean(exclude=None) #validate update params and raise exception if any
		update_params['updated_at'] = datetime.datetime.now().isoformat()
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
	create_params = request.get_json()
	try:
		session = Session(type_=create_params['type'], members=create_params['members'], category=create_params['category'], created_at=datetime.datetime.now().isoformat(), updated_at=datetime.datetime.now().isoformat(), description=create_params['description'], hours=create_params['hours'])
		session.save(force_insert=True)
	except Exception as e:
		message = 'User does not exists.' if str(e) == '' else str(e)
		return jsonify({'error': message, 'error_status': True}), 200
	return jsonify({'message': 'Successfully created session.', 'session_id': str(session._id), 'error_status': False}), 201

@app.route("/sessions/user", methods=['POST'])
def get_student_sessions():
	try:
		user_id = request.get_json()['user_id']
		User.objects.get({'_id':ObjectId(user_id)})
		sessions_list = []
		for session in Session.objects.all():
			session_users = session.members.copy()
			# code.interact(local=dict(globals(), **locals()))
			if (user_id in session_users) and (session.status in ["active", "ended"]) :
				mentor = session.mentor
				mentor_details = {'name': mentor.name, 'user_id': str(mentor._id), 'email': mentor.email, 'photo_url': mentor.photo_url}
				sessions_list.append({'session_id': str(session._id), 'type': session.type_, 'mentor': mentor_details, 'members': session.members, 'start_time':
							session.start_time, 'status': session.status, 'active_duration': session.active_duration, 'end_time': session.end_time,
							'feedback': session.feedback, 'category': session.category, 'created_at': session.created_at, 'updated_at': session.updated_at})
	except Exception as e:
		message = 'User does not exists.' if str(e) == '' else str(e)
		return jsonify({'error': message, 'error_status': True}), 404
	return jsonify({'sessions': sessions_list, 'error_status': False}), 200

@app.route("/sessions/mentor", methods=['POST'])
def get_mentor_sessions():
	try:
		user_id = request.get_json()['user_id']
		User.objects.get({'_id':ObjectId(user_id)})
		sessions_list = []
		for session in Session.objects.all():
			# code.interact(local=dict(globals(), **locals()))
			if session.mentor != None:
				if (user_id == str(session.mentor._id)) and (session.status in ["active", "ended"] ):
					mentor = session.mentor
					mentor_details = {'name': mentor.name, 'user_id': str(mentor._id), 'email': mentor.email, 'photo_url': mentor.photo_url}
					# get user deatils
					student_id = session.members[0]
					student = User.objects.get({'_id':ObjectId(student_id)})
					student_details = {'name': student.name, 'user_id': str(student._id), 'email': student.email, 'photo_url': student.photo_url}
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
						'feedback': session.feedback,
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
		mentor = User.objects.get({'_id':ObjectId(user_id)})
		preferences = mentor.preferences.copy()
		preferences.append('others')
		sessions_list = []
		for session in Session.objects.all():
			# code.interact(local=dict(globals(), **locals()))
			if (session.status == "inactive") and (session.category in preferences ):
				student_id = session.members[0]
				student_obj = User.objects.get({'_id':ObjectId(student_id)})
				student_details = {
					'name': student_obj.name,
					'user_id': str(student_obj._id),
					'email': student_obj.email,
					'photo_url': student_obj.photo_url
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
					'feedback': session.feedback,
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
		result = {
			'session_id': str(session._id),
			'type': session.type_,
			'members': session.members,
			'start_time': session.start_time,
			'status': session.status,
			'hours': session.hours,
			'active_duration': session.active_duration,
			'end_time': session.end_time,
			'feedback': session.feedback,
			'category': session.category,
			'created_at': session.created_at,
			'updated_at': session.updated_at,
			'mentor': {
				'name': mentor.name,
				'user_id': str(mentor._id),
				'email': mentor.email,
				'photo_url': mentor.photo_url
			} if mentor else {}
		}
		return jsonify(result), 200
	except Exception as e:
		message = 'Session does not exists.' if str(e) == '' else str(e)
		return jsonify({'error': message, 'error_status': True}), 404

@app.route("/session/update", methods=['PATCH'])
@app.route("/session/update/<string:action>", methods=['PATCH'])
def update_session(action=None):
	try:
		update_params = request.get_json()
		session_id = ObjectId(update_params['session_id'])
		session_ = Session.objects.get({'_id': session_id}) # validates if given session id is valid.
		session = Session.objects.raw({'_id': session_id})
		emit('session', jsonify({ 'action': action, 'session_id': session_id }), namespace='/')
		if action == "start" and session_.status == 'inactive':
			if update_params['mentor_id']:
				mentor = User.objects.get({'_id': ObjectId(update_params['mentor_id'])})
				if mentor.role != "mentor":
					raise ValidationError("Given mentor id is incorrect, the role of the user is 'student'.")
			else:
				raise ValidationError("Mentor id is required to start a session.")
			session.update({'$set': {"start_time": datetime.datetime.now().isoformat() , "updated_at": datetime.datetime.now().isoformat(), 'status': 'active', "mentor": mentor._id}})
		elif action == "end" and session_.status == 'active':
			end_time = datetime.datetime.now()
			# code.interact(local=dict(globals(), **locals()))
			seconds = (end_time - session_.start_time).total_seconds()
			hours = int(seconds // 3600)
			minutes = int((seconds % 3600) // 60)
			secs = int(seconds % 60)
			active_duration = '{}:{}:{}'.format(hours, minutes, secs)
			session.update({'$set': {"end_time": end_time.isoformat(), "active_duration": active_duration, "updated_at": datetime.datetime.now().isoformat(), 'status': 'ended'}})
		elif action == "kill" and session_.status == 'inactive':
			session.update({'$set': {"updated_at": datetime.datetime.now().isoformat(), 'status': 'lost'}})
		else:
			raise ValidationError("Presently the session is " + session_.status)
	except Exception as e :
		message = 'Session does not exists.' if str(e) == '' else str(e)
		return jsonify({'error': message, 'error_status': True}), 200
	return jsonify({'message': 'Successfully updated session.','error_status': False}), 202



# APIs for Message
@app.route("/message/create", methods=['POST'])
def create_message():
	try:
		create_params = request.get_json()
		create_params['created_at'] = datetime.datetime.now().isoformat()
		message = Message(session=create_params['session_id'], sender=create_params['sender_id'],
						content=create_params['content'], type_=create_params['type'], created_at=create_params['created_at'])
		message.save()
		emit('chat', jsonify(create_params), namespace='/')
	except Exception as e:
		return jsonify({"error": str(e), 'error_status': True}), 200
	return jsonify({'message': 'Successfully created a message.','error_status': False}), 201

@app.route("/messages", methods=['POST'])
def get_messages():
	try:
		session_id = ObjectId(request.get_json()['session_id'])
		session = Session.objects.get({'_id': session_id})
		result = []
		messages = Message.objects.raw({'session': session_id})
		for message in messages:
			user = message.sender
			sender_details = {"user_id": str(user._id), "name": user.name, "email": user.email, "role": user.role}
			result.append({"message_id": str(message._id), "session_id": str(message.session._id), "sender": sender_details,
			"content": message.content, "type": message.type_, "created_at":message.created_at})
	except Exception as e:
		message = 'Session does not exists.' if str(e) == '' else str(e)
		return jsonify({'error': message, 'error_status': True}), 404
	return jsonify({'messages': result, 'error_status': False}), 200

# APIs for Corporate Group

# @app.route("/corporate_group/create", methods=['POST'])
# def create_corporate_gropu():
#     try:
#         params = request.get_json()


if __name__ == '__main__':
	socketio.run(app)
	# app.run(port=3000, debug=True, host='localhost')
