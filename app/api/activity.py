import datetime
from flask import Blueprint, Flask, request, jsonify
from bson import ObjectId, errors
from pymongo.errors import DuplicateKeyError
from app.models.activity import *

main = Blueprint('activity', __name__)

@main.route("/activity/create", methods=['POST'])
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

@main.route("/activity/update", methods=['POST'])
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

@main.route("/activity", methods=['POST'])
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