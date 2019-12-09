from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError
from bson import ObjectId

class CorporateGroup(MongoModel):
    name = fields.CharField(required=True, mongo_name='name')
    code = fields.CharField(
        required=True, mongo_name='code', max_length=5, min_length=5)
    categories = fields.ListField(mongo_name='categories')

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'