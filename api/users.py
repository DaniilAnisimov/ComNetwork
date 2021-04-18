import requests
from flask import jsonify

from data import db_session
from flask_restful import abort, Resource, reqparse

from data.users import User

post_parser = reqparse.RequestParser()
post_parser.add_argument('name', required=True)
post_parser.add_argument('about', required=True)
post_parser.add_argument('email', required=True)
post_parser.add_argument('password', required=True)
post_parser.add_argument('banned', reqparse=False, type=bool)

put_parser = reqparse.RequestParser()
put_parser.add_argument('about', reqparse=False)
put_parser.add_argument('email', reqparse=False)
put_parser.add_argument('password', reqparse=False)
put_parser.add_argument('last_password', reqparse=False)
put_parser.add_argument('banned', reqparse=False, type=bool)


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User {user_id} not found")


class UserResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        if user.banned:
            return jsonify({"message": "This user was banned"})

        return jsonify({'user': user.to_dict(
            only=('id', 'name', 'about', 'rating', 'email', 'date'))})

    def put(self, user_id):
        abort_if_user_not_found(user_id)
        args = put_parser.parse_args()
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        for key, value in args.items():
            if key == "about":
                user.about = value
            elif key == "email":
                if session.query(User).filter(User.email == args['email']).first():
                    return jsonify()
                user.email = value
            if key == "password" and "last_password" in args:
                if user.check_password(args["last_password"]):
                    user.password = value
                else:
                    return jsonify()
            elif key == "banned":
                user.banned = value
        session.commit()
        return jsonify({'success': 'OK'})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        for news in user.news:
            requests.delete(f'http://localhost:8080/api/news/{news.id}')
        for comment in user.comments:
            session.delete(comment)
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})


class UserListResource(Resource):
    def get(self):
        session = db_session.create_session()
        user = session.query(User).all()
        return jsonify({'users': [item.to_dict(
            only=('id', 'name', 'about', 'rating',
                  'email', 'date')) for item in user]})

    def post(self):
        args = post_parser.parse_args()
        session = db_session.create_session()
        user = User()
        if session.query(User).filter(User.name == args['name']).first():
            return jsonify()
        elif session.query(User).filter(User.email == args['email']).first():
            return jsonify()
        user.name = args['name']
        user.about = args['about']
        user.email = args['email']
        user.set_password(args['password'])
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})
