from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields
from pymodm.errors import ValidationError
from bson import ObjectId
import code
from app.models.session import *
class Message(MongoModel):
    session = fields.ReferenceField(Session, required=False, mongo_name="session")
    sender = fields.ReferenceField(User, required=False, mongo_name="sender")
    content = fields.CharField(required=False, mongo_name="content")
    message_type = fields.CharField(required=False, mongo_name="message_type", choices=['text', 'image'])
    created_at = fields.DateTimeField(required=False, mongo_name="created_at")

    class Meta:
        write_concern = WriteConcern(j=True)
        ignore_unknown_fields = True
        connection_alias = 'onx-app'

    def clean(self):
        self.is_session_valid()
        self.is_sender_valid()
        # self.is_message_type_present()
        # self.is_content_present()

    def is_sender_valid(self):
        if self.sender != None:
            valid_sender_list = self.session.members
            valid_sender_list.append(str(self.session.mentor._id))
            if (str(self.sender._id) in valid_sender_list) or self.sender.role == "admin":
                pass
            else:
                raise ValidationError("The sender is not a part of the given session.")
        # else:
        #     raise ValidationError("Sender id is missing.")


    def is_session_valid(self):
        if self.session != None:
            if self.session.status not in  ['active', 'accepted']:
                raise ValidationError("Session is not active/accepted.")
        # else:
        #     raise ValidationError("Session id is missing.")

    def is_content_present(self):
        if self.content == None:
            raise ValidationError("Message content cannot be blank.")

    def is_message_type_present(self):
        if self.message_type == None:
            raise ValidationError("Message type cannot be blank.")