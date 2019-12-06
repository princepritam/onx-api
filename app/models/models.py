from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError
from bson import ObjectId
import code


class CorporateGroup(MongoModel):
    name = fields.CharField(required=True, mongo_name='name')
    code = fields.CharField(
        required=True, mongo_name='code', max_length=5, min_length=5)
    categories = fields.ListField(mongo_name='categories')

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'


# user model
class User(MongoModel):
    email = fields.EmailField(required=False, mongo_name='email')
    name = fields.CharField(required=False, mongo_name='name')
    mobile_no = fields.CharField(min_length=10, max_length=10, required=False, mongo_name='mobile_no')
    role = fields.CharField(choices=('mentor', 'student', 'admin'), required=False, mongo_name='role')
    photo_url = fields.CharField(mongo_name='photo_url', default=None)
    uploaded_photo_url = fields.CharField(mongo_name='uploaded_photo_url', default=None)
    user_token = fields.CharField(mongo_name='user_token')
    user_group = fields.CharField(mongo_name='user_group', default=None)
    nickname = fields.CharField(mongo_name='nickname')
    preferences = fields.ListField(mongo_name='preferences')
    created_at = fields.DateTimeField(mongo_name='created_at')
    updated_at = fields.DateTimeField(mongo_name='updated_at')
    linkedin = fields.CharField(mongo_name='linkedin')
    certificates = fields.CharField(mongo_name='certificates')
    courses = fields.CharField(mongo_name='courses')
    background = fields.CharField(mongo_name='background')
    mentor_verified = fields.BooleanField(mongo_name='mentor_verified', default=False)
    hours_per_day = fields.CharField(mongo_name='hours_per_day')
    login_status = fields.BooleanField(mongo_name='login_status', default=True)

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'
        final = True

    def clean(self):
        if self.email != None:
            self.check_duplicate_user()
        # self.validate_user_group()

    def check_duplicate_user(self):
        try:
            User.objects.get({'email': self.email})
            raise ValidationError('User with this email already exist')
        except User.DoesNotExist:
            pass

    def validate_user_group(self):
        try:
            code.interact(local=dict(globals(), **locals()))
            if self.user_group != None:
                CorporateGroup.objects.get({'code': self.user_group})
            else:
                pass
        except Exception as e:
            message = "Invalid corporate code." if str(e) == "" else str(e)
            raise ValidationError(message)


# session model
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
    status = fields.CharField(choices=['active', 'accepted', 'inactive', 'ended', 'lost'], mongo_name='status', default='inactive')
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


# message model
class Message(MongoModel):
    session = fields.ReferenceField(Session, required=True, mongo_name="session")
    sender = fields.ReferenceField(User, required=True, mongo_name="sender")
    content = fields.CharField(required=True, mongo_name="content")
    type_ = fields.CharField(required=True, mongo_name="type", choices=['text', 'image'])
    created_at = fields.DateTimeField(required=True, mongo_name="created_at")

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'

    def clean(self):
        self.is_session_valid()
        self.is_sender_valid()

    def is_sender_valid(self):
        valid_sender_list = self.session.members
        valid_sender_list.append(str(self.session.mentor._id))
        # code.interact(local=dict(globals(), **locals()))
        if self.sender:
            if (str(self.sender._id) in valid_sender_list) or self.sender.role == "admin":
                pass
            else:
                raise ValidationError(
                    "The sender is not a part of the given session.")
        else:
            raise ValidationError("Given Sender ID does not exists.")

    def is_session_valid(self):
        if not self.session:
            raise ValidationError("Given Session ID does not exists.")
        else:
            if self.session.status != 'active':
                raise ValidationError("Session is not active.")
        return True

class Activity(MongoModel):
    user_id = fields.CharField(mongo_name='user_id')
    session_id = fields.CharField(mongo_name='session_id')
    is_dynamic = fields.BooleanField(mongo_name='is_dynamic')
    content = fields.CharField(mongo_name='content')
    created_at = fields.DateTimeField(required=False, mongo_name='created_at')
    updated_at = fields.DateTimeField(mongo_name='updated_at')
    
 
    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'
    
    def clean(self):
        # self.validate_user()
        pass

    def validate_user(self):
        try:
            if self.user_id != None:
                user = User.objects.get({'_id': ObjectId(self.user_id)})
            # else:
            #     raise ValidationError("user_id is mandatory for creating an activity.")
        except Exception as e:
            message = 'User does not exists' if str(e) == "" else str(e)
            raise ValidationError(message)
