from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError
from bson import ObjectId
from app.models.user import *
import code

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