from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError

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
        raise ValidationError('Given user is not having role as mentor')

def validate_student(user):
    if not user.role == 'student':
        raise ValidationError('Given user is not having role as student')

class Session(MongoModel):
    type_ = fields.CharField(required=True, choices=['single','multiple'], mongo_name='type')
    mentor = fields.ReferenceField(User, mongo_name='mentor', validators=[validate_mentor])
    student = fields.ReferenceField(User, mongo_name='student', validators=[validate_student])
    members = fields.ListField(mongo_name='members')
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