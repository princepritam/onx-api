from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError
from bson import ObjectId
# import code

class CorporateGroup(MongoModel):
    code = fields.CharField(required=True, mongo_name='code', max_length=5, min_length=5)
    categories = fields.ListField(mongo_name='categories')

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'

    def clean(self):
        self.validate_code()

    def validate_code(self):
        try:
            CorporateGroup.objects.get({'code': self.code})
            raise ValidationError('Code already exists.')
        except CorporateGroup.DoesNotExist:
            pass