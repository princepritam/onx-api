from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from app.models import User

class Session(MongoModel):
    mentor = fields.ReferenceField(User, mongo_name='mentor')
    student = fields.ReferenceField(User, mongo_name='mentor')

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'onx-app'