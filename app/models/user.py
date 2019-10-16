from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError

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