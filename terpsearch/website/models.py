# from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


# class User(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(150), unique=True)
#     password = db.Column(db.String(150))
#     first_name = db.Column(db.String(150))

class User(UserMixin):
    def __init__(self, user_id, email, bsky_email, first_name, password_hash):
        self.id = user_id
        self.email = email
        self.bsky_email = bsky_email
        self.first_name = first_name
        self.password_hash = password_hash
