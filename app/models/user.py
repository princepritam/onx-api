from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError
from bson import ObjectId
import code

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