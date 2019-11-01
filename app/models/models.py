from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError
from bson import ObjectId

#user model
class User(MongoModel):
    email = fields.EmailField(required=False, mongo_name='email')
    name = fields.CharField(required=False, mongo_name='name')
    mobileNo = fields.CharField(min_length=10, max_length=10, required=False, mongo_name='mobileNo')
    role = fields.CharField(choices=('mentor', 'student', 'admin'), required=False, mongo_name='role')
    created_at = fields.DateTimeField(mongo_name='created_at')
    updated_at = fields.DateTimeField(mongo_name='updated_at')

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'
        final = True
    def clean(self):
        try:
            User.objects.get({'email':self.email})
            raise ValidationError('User with this email already exist')
        except User.DoesNotExist:
            pass

#session model
def validate_mentor(user):
    if not user.role == 'mentor':
        raise ValidationError('Given user is not a mentor')

def validate_student(user):
    if not user.role == 'student':
        raise ValidationError('Given user/users is not a student')

def validate_user(user_ids):
    try:
        for id_ in user_ids:
            user = User.objects.get({"_id" : ObjectId(id_)})
            validate_student(user)
    except(User.DoesNotExists):
        raise ValidationError("User/Users does not exits.")
                

class Session(MongoModel):
    type_ = fields.CharField(required=True, choices=['single','multiple'], mongo_name='type')
    mentor = fields.ReferenceField(User, mongo_name='mentor', validators=[validate_mentor])
    members = fields.ListField(mongo_name='members', validators=[])
    status = fields.CharField(choices=('active', 'inactive'), mongo_name='status')
    start_time = fields.DateTimeField(required=False, mongo_name='start_time')
    duration = fields.TimestampField(mongo_name='duration')
    end_time = fields.DateTimeField(mongo_name='end_time')
    feedback = fields.CharField(max_length=1000, mongo_name='feed_back')
    created_at = fields.DateTimeField(required=True, mongo_name='created_at')
    updated_at = fields.DateTimeField(mongo_name='updated_at')
    
    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'
    

    def clean(self):
        if self.type_ == 'multiple' and len(self.members) < 2:
            raise ValidationError("Atleast two members are required to start a multiple session.")