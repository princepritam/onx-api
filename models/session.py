from pymodm.connection import connect
# Connect to MongoDB and call the connection "onx".
connect("mongodb://localhost:27017/onx", alias="onx-app")
from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields

class Session(MongoModel):
    email = fields.EmailField(primary_key=True)
    first_name = fields.CharField()
    last_name = fields.CharField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'onx-app'
# import datetime as dt
# from dataclasses import dataclass
# from marshmallow import Schema, fields
# from models.user import UserSchema

# @dataclass
# class Session():
#     def __init__(self, id_):
#         self.session_id = id_
#         self.start_time = None
#         self.end_time = None
#         self.mentor = None
#         self.student = None
#         self.duration = None

#     def startSession(self):
#         self.start_time = dt.datetime.now()

#     def endSession(self):
#         self.end_time = dt.datetime.now()
#         self.duration = self.end_time - self.start_time

#     @classmethod
#     def get_session(cls,**sessiondata):
#         sessiondata_ = {key:value for key,value in sessiondata.items() if key != "_id"}
#         session = cls(sessiondata['session_id'])
#         for key,value in sessiondata_.items():
#             session.key = value
#         return session
        

# class SessionSchema(Schema):
#     session_id = fields.Int(primary_key = True)
#     start_time = fields.DateTime()
#     end_time = fields.DateTime()
#     mentor = fields.Nested(UserSchema)
#     student = fields.Nested(UserSchema)
#     duration = fields.DateTime()