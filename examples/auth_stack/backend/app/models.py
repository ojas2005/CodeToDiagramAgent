from sqlalchemy import Column, ForeignKey, Integer, String


class User:
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)


class Session:
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
