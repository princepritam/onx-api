# APIs for Corporate Group
import datetime
from flask import Blueprint, request, jsonify
from bson import ObjectId, errors
from pymongo.errors import DuplicateKeyError
from app.models.user import *

main = Blueprint('corporate_group', __name__)

@main.route("/corporate/create", methods=['POST'])
def create_corporate_group():
    try:
        params = request.get_json()
        CorporateGroup(code=params['code'], categories=params['categories']).save(full_clean=True)
    except Exception as e:
        return jsonify({'error': str(e), 'error_status': True}), 404
    return jsonify({'message': "Successfully created group.", "error_status": False}), 201


@main.route("/user/corporate", methods=["POST"])
def get_corporate_for_user():
    try:
        user = User.objects.get({'_id': ObjectId(request.get_json()['user_id'])})
        group = CorporateGroup.objects.get({"_id": ObjectId(user.user_group)})
        return jsonify({"code": group.code, "categories": group.categories, "id": str(group._id)}), 200
    except Exception as e:
        message = 'User does not exists.' if str(e) == '' else str(e)
        return jsonify({'error': message, 'error_status': True}), 404

@main.route("/corporates", methods=["GET"])
def get_all_codes():
    groups = CorporateGroup.objects.all()
    data = []
    for group in groups:
        data.append({"code": group.code, "categories": group.categories, "id": str(group._id)})
    return jsonify({"corporates": data}), 200
