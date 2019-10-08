from mongoengine import *

class User(Document):
    ROLES = (('M', 'Mentor'),
        ('U', 'User'),
        ('A', 'Admin'))
    name = StringField(required=True)
    token = StringField(required=True,max_length=50)
    role = StringField(required=True,choices=ROLES)
    meta = {'allow_inheritance': True}


class Mentor(User):
    domains = ListField(StringField(max_length=30))


