from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields

class Session(MongoModel):
    pass

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'onx-app'