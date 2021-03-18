import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Comment(SqlAlchemyBase):
    __tablename__ = "comments"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, index=True)
    text = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    rating = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    news_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("news.id"))
    banned = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now())

    user = orm.relation("User")
    news = orm.relation("News")
