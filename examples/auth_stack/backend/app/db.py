"""In-memory user lookup for the architecture fixture."""

USERS = {"demo": {"id": 1, "password": "password"}}


def get_user(username):
    return USERS.get(username)
