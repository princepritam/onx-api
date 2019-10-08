from flask_login import UserMixin
import pymongo

from db import db


class User(UserMixin):
    def __init__(self, id_, name, email, role):
        self.id = id_
        self.name = name
        self.email = email
        self.role = role

    def asdict(self):
        return {
            'id_': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role
        }

    @classmethod
    def get(cls, user_id):
        user = db.users.find_one({"id_": user_id})
        if user:
            _, id_, name, email, role = user
            return cls(id_, name, email, role)
        return None

    @classmethod
    def create(cls, id_, name, email, role):
        user = cls(id_, name, email, role)
        db.users.insert_one(user.asdict())
