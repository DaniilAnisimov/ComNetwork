from flask import jsonify

from data import db_session
from flask_restful import abort, Resource, reqparse
from news import abort_if_news_not_found
from users import abort_if_user_not_found

from data.comments import Comment

post_parser = reqparse.RequestParser()
post_parser.add_argument('content', required=True)
post_parser.add_argument('user_id', required=True, type=int)
post_parser.add_argument('news_id', required=True, type=int)

put_parser = reqparse.RequestParser()
put_parser.add_argument('rating')
put_parser.add_argument('banned', type=bool)


def abort_if_comment_not_found(comment_id):
    session = db_session.create_session()
    comment = session.query(Comment).get(comment_id)
    if not comment:
        abort(404, message=f"Comment {comment_id} not found")


class CommentResource(Resource):
    def get(self, comment_id):
        abort_if_comment_not_found(comment_id)
        session = db_session.create_session()
        comment = session.query(Comment).get(comment_id)
        if comment.banned:
            return jsonify({"message": "This comment was banned"})
        return jsonify({'comment': comment.to_dict(
            only=('id', 'content', 'rating', 'user_id', 'news_id', 'date'))})

    def put(self, comment_id):
        abort_if_comment_not_found(comment_id)
        args = put_parser.parse_args()
        session = db_session.create_session()
        comment = session.query(Comment).get(comment_id)
        for key, value in args.items():
            if key == "content":
                comment.content = value
            elif key == "banned":
                comment.banned = value
        session.commit()
        return jsonify({'success': 'OK'})

    def delete(self, comment_id):
        abort_if_comment_not_found(comment_id)
        session = db_session.create_session()
        comment = session.query(Comment).get(comment_id)
        session.delete(comment)
        session.commit()
        return jsonify({'success': 'OK'})


class CommentListResource(Resource):
    def get(self):
        session = db_session.create_session()
        comment = session.query(Comment).all()
        return jsonify({'comments': [item.to_dict(
            only=('id', 'content', 'rating', 'user_id', 'news_id', 'date')) for item in comment
            if not item.banned]})

    def post(self):
        args = post_parser.parse_args()
        session = db_session.create_session()
        abort_if_user_not_found(args['user_id'])
        abort_if_news_not_found(args['news_id'])
        comment = Comment(args['content'], args['user_id'], args['news_id'])
        session.add(comment)
        session.commit()
        return jsonify({'success': 'OK'})
