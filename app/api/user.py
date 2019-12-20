# APIs for User
import datetime, code
from flask import Blueprint, request, jsonify
from bson import ObjectId, errors
from pymongo.errors import DuplicateKeyError
from app.models.user import *

main = Blueprint('user', __name__)

@main.route("/user/create", methods=['POST'])
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


@main.route("/users", methods=['GET'])
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


@main.route("/user", methods=['POST'])
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


@main.route("/user/update", methods=['PATCH'])
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
        if str(e) == "'user_group'":
            user.update({'$set': update_params})
            return jsonify({'message': 'User updated successfully.', 'error_status': False}), 202
        # code.interact(local=dict(globals(), **locals()))
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 422
    return jsonify({'message': 'User updated successfully.', 'error_status': False}), 202


@main.route("/user/delete", methods=['DELETE'])
def delete_user():
    try:
        user_id = ObjectId(request.get_json()['user_id'])
        User.objects.get({'_id': user_id}).delete()
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 200
    return jsonify({'message': 'User deleted from database.', 'error_status': False}), 202
