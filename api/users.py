import json

from flask import jsonify

from data import db_session
from flask_restful import abort, Resource, reqparse

from data.users import User

from re import *


# Вызовем ошибку в случае если id пользователя не было найдено в бд
def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User {user_id} not found")


# Инициализируем api key для проверки доступа к нашему api
with open("settings.json") as file:
    api_key = json.load(file)["api"]["api_key"]


def checking_api_key(key):
    if key != api_key:
        abort(401, message="api_key fails validation")


# Проверяем действительность почтового адреса
def checking_email(email):
    pattern = compile("(^|\s)[-a-z0-9_.]+@([-a-z0-9]+\.)+[a-z]{2,6}(\s|$)")
    return pattern.match(email)


def checking_password(password):
    if len(password) < 10:
        return {"Error": {"message": "Длина пароля менее 10 символов"}}
    elif not any(map(lambda x: x.isdigit(), password)):
        return {"Error": {"message": "В пароле нет цифр"}}
    elif not any(map(lambda x: x.islower(), password)):
        return {"Error": {"message": "В пароле нет букв в нижнем регистре"}}
    elif not any(map(lambda x: x.isupper(), password)):
        return {"Error": {"message": "В пароле нет букв в верхнем регистре"}}
    else:
        return {'success': 'OK'}


# Создаём парсер для put запроса
put_parser = reqparse.RequestParser()
put_parser.add_argument('about', required=False)
put_parser.add_argument('email', required=False)
put_parser.add_argument('password', required=False)
put_parser.add_argument('last_password', required=False)
put_parser.add_argument('rating', required=False, type=int)
put_parser.add_argument('banned', required=False, type=bool)


class UserResource(Resource):
    def get(self, user_id, key):
        checking_api_key(key)
        abort_if_user_not_found(user_id)

        session = db_session.create_session()
        user = session.query(User).filter(User.id == user_id).first()
        if user.banned:
            return jsonify({"Error": {"message": "Этот пользователь был забанен"}})
        return jsonify({'user': user.to_dict(
            only=('id', 'name', 'about', 'rating', 'email', 'date'))})

    def put(self, user_id, key):
        checking_api_key(key)
        abort_if_user_not_found(user_id)

        args = put_parser.parse_args()

        session = db_session.create_session()
        user = session.query(User).filter(User.id == user_id).first()

        # Проверяем данные
        if not (args["email"] is None):
            if session.query(User).filter(User.email == args["email"]).first():
                return jsonify({"Error": {"message": "Этот email занят"}})
            if not checking_email(args["email"]):
                return jsonify({"Error": {"message": "Электронная почта не действительна"}})
        if not (args["password"] is None):
            if args["last_password"] is None:
                return jsonify({"Error": {"message": "Прошлый пароль отсутствует"}})
            cp = checking_password(args["password"])
            if 'success' not in cp:
                return jsonify(cp)
            if not user.check_password(args["last_password"]):
                return jsonify({"Error": {"message": "Пароли не совпадают"}})

        for key, value in args.items():
            if not (value is None):
                if key == "about":
                    user.about = value
                elif key == "email":
                    user.email = value
                elif key == "password":
                    user.set_password(value)
                elif key == "banned":
                    user.banned = value
                elif key == "rating":
                    user.rating = value

        session.commit()
        return jsonify({'success': 'OK'})

    def delete(self, user_id, key):
        checking_api_key(key)
        abort_if_user_not_found(user_id)

        session = db_session.create_session()
        user = session.query(User).filter(User.id == user_id).first()
        # До удаления пользователя удалим все его посты и комментарии к этим постам
        for news in user.news:
            for comment in news.comments:
                session.delete(comment)
            session.delete(news)
        for comment in user.comments:
            session.delete(comment)
        # Удаляем пользователя
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})


# Создаём парсер для post запроса
post_parser = reqparse.RequestParser()
post_parser.add_argument('name', required=True)
post_parser.add_argument('about', required=True)
post_parser.add_argument('email', required=True)
post_parser.add_argument('password', required=True)


class UserListResource(Resource):
    def get(self, key):
        checking_api_key(key)
        session = db_session.create_session()
        users = session.query(User).all()
        return jsonify({'users': [item.to_dict(
            only=('id', 'name', 'about', 'rating', 'email', 'date')) for item in users if not item.banned]})

    def post(self, key):
        checking_api_key(key)

        args = post_parser.parse_args()

        session = db_session.create_session()
        user = User()
        if session.query(User).filter(User.name == args['name']).first():
            return jsonify({"Error": {"message": "Пользователь с таким именем уже существует"}})

        if session.query(User).filter(User.email == args['email']).first():
            return jsonify({"Error": {"message": "Этот email занят"}})
        if not checking_email(args["email"]):
            return jsonify({"Error": {"message": "Электронная почта не действительна"}})

        cp = checking_password(args["password"])
        if 'success' not in cp:
            return jsonify(cp)
        # Добавляем нового пользователя
        user.name = args['name']
        user.about = args['about']
        user.email = args['email']
        user.set_password(args['password'])
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})
