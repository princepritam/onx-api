from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields

class User(MongoModel):
    email = fields.EmailField(primary_key=True)
    name = fields.CharField()
    mobileNo = fields.CharField(min_length=10, max_length=10)
    role = fields.CharField(choices=('mentor', 'student'))

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'onx-app'
