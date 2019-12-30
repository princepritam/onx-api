from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError
from bson import ObjectId
import code
from app.models.user import *

def validate_mentor(user):
    if user:
        if not user.role == 'mentor':
            raise ValidationError('Given user is not a mentor')
    else:
        raise ValidationError('Mentor ID is invalid.')


def validate_student(user):
    if not user.role == 'student':
        raise ValidationError('Given user/users is not a student')


def validate_users(user_ids):
    try:
        for id_ in user_ids:
            user = User.objects.get({"_id": ObjectId(id_)})
            validate_student(user)
    except Exception as e:
        message = "User does not exists." if str(e) == "" else str(e)
        raise ValidationError(message)

class Session(MongoModel):
    type_ = fields.CharField(required=False, choices=['single', 'multiple'], mongo_name='type')
    mentor = fields.ReferenceField(User, mongo_name='mentor', validators=[validate_mentor])
    members = fields.ListField(mongo_name='members', validators=[validate_users], required=False)
    status = fields.CharField(choices=['scheduled_inactive', 'scheduled_active', 'active', 'accepted', 'inactive', 'ended', 'lost'], mongo_name='status', default='inactive')
    start_time = fields.DateTimeField(required=False, mongo_name='start_time')
    category = fields.CharField(mongo_name='category', required=False)
    description = fields.CharField(mongo_name='description')
    active_duration = fields.CharField(mongo_name='active_duration')
    hours = fields.IntegerField(mongo_name='hours', default=1)
    end_time = fields.DateTimeField(mongo_name='end_time')
    user_feedback = fields.CharField(max_length=1000, mongo_name='user_feedback')
    mentor_feedback = fields.CharField(max_length=1000, mongo_name='mentor_feedback')
    user_rating = fields.IntegerField(mongo_name='user_rating')
    mentor_rating = fields.IntegerField(mongo_name='mentor_rating')
    created_at = fields.DateTimeField(required=False, mongo_name='created_at')
    updated_at = fields.DateTimeField(mongo_name='updated_at')
    scheduled_time = fields.DateTimeField(required=False, mongo_name='scheduled_time')

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'

    def clean(self):
        self.validate_type()

    def validate_type(self):
        if self.type_ != None:
            if self.type_ == 'multiple' and len(self.members) < 2:
                raise ValidationError(
                    "Atleast two members are required to start a multiple session.")
            if self.type_ == 'single' and len(self.members) > 1:
                raise ValidationError("Only one member is allowed in single mode.")


