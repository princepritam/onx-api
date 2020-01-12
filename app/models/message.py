from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError
from bson import ObjectId
import code
from app.models.session import *
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
                raise ValidationError("The sender is not a part of the given session.")
        else:
            raise ValidationError("Given Sender ID does not exists.")

    def is_session_valid(self):
        if not self.session:
            raise ValidationError("Given Session ID does not exists.")
        else:
            if self.session.status not in  ['active', 'accepted']:
                raise ValidationError("Session is not active/accepted.")
        return True