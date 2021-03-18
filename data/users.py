import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = "users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, index=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    about = sqlalchemy.Column(sqlalchemy.String)
    rating = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    address = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now())
    banned = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    news = orm.relation("News", back_populates="user")
    comments = orm.relation("Comment", back_populates="user")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
