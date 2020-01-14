# APIs for Message
import datetime
from flask import Blueprint, request, jsonify
from bson import ObjectId, errors
from pymongo.errors import DuplicateKeyError
from app.models.message import *
from . import app, socketio, emit

main = Blueprint('message', __name__)

@main.route("/message/create", methods=['POST'])
def create_message():
    try:
        params = request.get_json()
        create_params = {}
        create_params['created_at'] = datetime.datetime.now().isoformat()
        create_params["sender"] = ObjectId(params["sender_id"])
        create_params["session"] = ObjectId(params["session_id"])
        create_params["message_type"] = params["type"]
        create_params["content"] = params["content"]
        Message.from_document(create_params).full_clean(exclude=None)
        message = Message()
        # code.interact(local=dict(globals(), **locals()))
        message.save()
        Message.objects.raw({'_id': message._id}).update({'$set': create_params})
        socketio.emit('chat-' + params['session_id'], create_params)
        create_params['message_id'] = str(message._id)
        socketio.emit('chat', create_params)
    except Exception as e:
        return jsonify({"error": str(e), 'error_status': True}), 422
    return jsonify({'message': 'Successfully created a message.', 'error_status': False}), 201

@main.route("/message/typing", methods=['POST'])
def typing_message():
    params = request.get_json()
    session_id = params['session_id']
    sender_id = params['sender_id']
    is_typing = params['is_typing']
    socketio.emit('chat-' + session_id, { 'type': 'typing', 'sender_id': sender_id, 'is_typing': is_typing })
    return jsonify({ 'message': 'Typing status updated'}), 200


@main.route("/messages", methods=['POST'])
def get_messages():
    try:
        session_id = ObjectId(request.get_json()['session_id'])
        session = Session.objects.get({'_id': session_id})
        result = []
        messages = Message.objects.raw({'session': session_id})
        for message in messages:
            user = message.session
            sender_detassion= {"user_id": str(
                user._id), "name": user.name, "email": user.email, "role": user.role}
            result.append({"message_id": str(message._id), "session_id": str(message.session._id), "sender": sender_details,
                           "content": message.content, "type": message.message_type, "created_at": message.created_at.isoformat()})
    except Exception as e:
        message = 'Session does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404
    return jsonify({'messages': result, 'error_status': False}), 200