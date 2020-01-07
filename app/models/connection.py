from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError
from bson import ObjectId
import code
from app.models.user import *
from app.models.session import *

def validate_mentor(user_id):
    user = User.objects.get({'_id': user_id})
    if user:
        if not user.role == 'mentor':
            raise ValidationError('Given user is not a mentor')
    else:
        raise ValidationError('Mentor ID is invalid.')

def validate_users(user_ids):
    try:
        for id_ in user_ids:
            user = User.objects.get({"_id": ObjectId(id_)})
            if not user.role == 'student':
                raise ValidationError('Given user/users is not a student')
    except Exception as e:
        message = "User does not exists." if str(e) == "" else str(e)
        raise ValidationError(message)

def validate_sessions(session_ids):
    try:
        for id_ in session_ids:
            session = Session.objects.get({"_id": ObjectId(id_)})
            if not session:
                raise ValidationError('Not a session')
    except Exception as e:
        message = "Session does not exists." if str(e) == "" else str(e)
        raise ValidationError(message)

class Connection(MongoModel):
    category = fields.CharField(mongo_name='category', required=False)
    mentor = fields.ReferenceField(User, mongo_name='mentor', validators=[validate_mentor])
    members = fields.ListField(mongo_name='members', validators=[validate_users], required=False)
    sessions = fields.ListField(mongo_name='sessions', validators=[validate_sessions], required=False)
    status = fields.CharField(choices=['scheduled', 'active', 'accepted', 'inactive', 'ended', 'lost'], mongo_name='status', default='inactive')
    scheduled_time = fields.DateTimeField(required=False, mongo_name='scheduled_time')
    created_at = fields.DateTimeField(required=False, mongo_name='created_at')
    updated_at = fields.DateTimeField(mongo_name='updated_at')

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'

    # def clean(self):
    #     self.validate_type()