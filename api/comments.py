import json

from flask import jsonify

from data import db_session
from flask_restful import abort, Resource, reqparse
from api.news import abort_if_news_not_found
from api.users import abort_if_user_not_found

from data.comments import Comment


def abort_if_comment_not_found(comment_id):
    session = db_session.create_session()
    comment = session.query(Comment).get(comment_id)
    if not comment:
        abort(404, message=f"Comment {comment_id} not found")


# Инициализируем api key для проверки доступа к нашему api
with open("settings.json") as file:
    api_key = json.load(file)["api"]["api_key"]


def checking_api_key(key):
    if key != api_key:
        abort(401, message="api_key fails validation")


put_parser = reqparse.RequestParser()
put_parser.add_argument('rating', required=False, type=int)
put_parser.add_argument('banned', required=False, type=bool)


class CommentResource(Resource):
    def get(self, comment_id, key):
        checking_api_key(key)
        abort_if_comment_not_found(comment_id)

        session = db_session.create_session()
        comment = session.query(Comment).filter(Comment.id == comment_id).first()
        if comment.banned:
            return jsonify({"message": "This comment was banned"})
        return jsonify({'comment': comment.to_dict(
            only=('id', 'content', 'rating', 'user_id', 'news_id', 'date'))})

    def put(self, comment_id, key):
        checking_api_key(key)
        abort_if_comment_not_found(comment_id)

        args = put_parser.parse_args()
        session = db_session.create_session()
        comment = session.query(Comment).filter(Comment.id == comment_id).first()
        for key, value in args.items():
            if not (value is None):
                if key == "rating":
                    comment.rating = value
                elif key == "banned":
                    comment.banned = value
        session.commit()
        return jsonify({'success': 'OK'})

    def delete(self, comment_id, key):
        checking_api_key(key)
        abort_if_comment_not_found(comment_id)

        session = db_session.create_session()
        comment = session.query(Comment).filter(Comment.id == comment_id).first()
        session.delete(comment)
        session.commit()
        return jsonify({'success': 'OK'})


post_parser = reqparse.RequestParser()
post_parser.add_argument('content', required=True)
post_parser.add_argument('user_id', required=True, type=int)
post_parser.add_argument('news_id', required=True, type=int)


class CommentListResource(Resource):
    def get(self, key):
        checking_api_key(key)

        session = db_session.create_session()
        comments = session.query(Comment).all()
        return jsonify({'comments': [item.to_dict(
            only=('id', 'content', 'rating', 'user_id', 'news_id', 'date')) for item in comments
            if not item.banned]})

    def post(self, key):
        checking_api_key(key)

        args = post_parser.parse_args()
        session = db_session.create_session()
        abort_if_user_not_found(args['user_id'])
        abort_if_news_not_found(args['news_id'])
        comment = Comment()
        comment.content = args['content']
        comment.user_id = args['user_id']
        comment.news_id = args['news_id']
        session.add(comment)
        session.commit()
        return jsonify({'success': 'OK'})
