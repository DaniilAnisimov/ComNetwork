from flask import jsonify

from data import db_session
from data.news import News
from flask_restful import abort, Resource, reqparse

from data.users import User

parser = reqparse.RequestParser()
parser.add_argument('name', required=True)
parser.add_argument('content', required=True)
parser.add_argument('user_id', required=True, type=int)
parser.add_argument('tags', required=True)

put_parser = reqparse.RequestParser()
put_parser.add_argument('name')
put_parser.add_argument('content')
put_parser.add_argument('tags')
put_parser.add_argument('banned', reqparse=False, type=bool)


def abort_if_news_not_found(news_id):
    session = db_session.create_session()
    news = session.query(News).get(news_id)
    if not news:
        abort(404, message=f"News {news_id} not found")


class NewsResource(Resource):
    def get(self, news_id):
        abort_if_news_not_found(news_id)
        session = db_session.create_session()
        news = session.query(News).get(news_id)
        if news.banned:
            return jsonify({"message": "This news was banned"})
        return jsonify({'news': news.to_dict(
            only=('id', 'name', 'rating', 'content', 'user_id', 'date'))})

    def put(self, news_id):
        abort_if_news_not_found(news_id)
        args = parser.parse_args()
        session = db_session.create_session()
        news = session.query(News).get(news_id)
        for key, value in args.items():
            if key == "name":
                news.name = value
            elif key == "content":
                news.content = value
            elif key == "tags":
                news.tags = value
            elif key == "banned":
                news.banned = value
        session.commit()
        return jsonify({'success': 'OK'})

    def delete(self, news_id):
        abort_if_news_not_found(news_id)
        session = db_session.create_session()
        news = session.query(News).get(news_id)
        for comment in news.comments:
            session.delete(comment)
        session.delete(news)
        session.commit()
        return jsonify({'success': 'OK'})


class NewsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        news = session.query(News).all()
        return jsonify({'news': [item.to_dict(
            only=('id', 'name', 'rating', 'content', 'user_id', 'date')) for item in news]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        user = session.query(User).filter(User.id == args['user_id']).first()
        if user:
            news = News(
                name=args['name'],
                text=args['content'],
                user_id=args['user_id'],
                tags=args['tags'],
            )
        else:
            return jsonify({"message": "Creator not found"})
        session.add(news)
        session.commit()
        return jsonify({'success': 'OK'})
