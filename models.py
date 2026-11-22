from flask_login import UserMixin

from utils.db import db


class User(UserMixin):
    def __init__(self, id, username, email, pwd_hash):
        self.id = id
        self.username = username
        self.email = email
        self.hash = pwd_hash

    def get_id(self):
        return str(self.id)


def get_user_by_id(user_id):
    rows = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    return create_user(rows)


def get_user_by_username(username):
    rows = db.execute("SELECT * FROM users WHERE username = ?", username)
    return create_user(rows)


def create_user(rows):
    if rows:
        row = rows[0]
        return User(row["id"], row["username"], row["email"], row["pwd_hash"])
    return None