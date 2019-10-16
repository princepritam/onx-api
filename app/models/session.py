from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from app.models import User

class Session(MongoModel):
    mentor = fields.ReferenceField(User, mongo_name='mentor')
    student = fields.ReferenceField(User, mongo_name='student')
    start_time = fields.DateTimeField(mongo_name='start_time')
    duration = fields.TimestampField(mongo_name='duration')
    end_time = fields.DateTimeField(mongo_name='end_time')
    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'