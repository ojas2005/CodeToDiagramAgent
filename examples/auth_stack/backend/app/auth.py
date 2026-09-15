from .db import get_user


def authenticate(username, password):
    user = get_user(username)
    return user if user and user["password"] == password else None


def create_session(user_id):
    return "session-{}".format(user_id)
