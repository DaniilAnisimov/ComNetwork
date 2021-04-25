import json

from flask import jsonify

from data import db_session
from data.news import News
from data.categories import Category
from flask_restful import abort, Resource, reqparse
from api.users import abort_if_user_not_found


# Вызовем ошибку в случае если id новости не было найдено в бд
def abort_if_news_not_found(news_id):
    session = db_session.create_session()
    news = session.query(News).get(news_id)
    if not news:
        abort(404, message=f"News {news_id} not found")


# Инициализируем api key для проверки доступа к нашему api
with open("settings.json") as file:
    api_key = json.load(file)["api"]["api_key"]


def checking_api_key(key):
    if key != api_key:
        abort(401, message="api_key fails validation")


# Создаём парсер для put запроса
put_parser = reqparse.RequestParser()
put_parser.add_argument('name', required=False)
put_parser.add_argument('rating', required=False, type=int)
put_parser.add_argument('content', required=False)
put_parser.add_argument('category', required=False)
put_parser.add_argument('banned', required=False, type=bool)
put_parser.add_argument("who_likes_it", required=False)


class NewsResource(Resource):
    def get(self, news_id, key):
        """{news: {'id':, 'name':, 'rating':, 'content':, 'date':, "who_likes_it":, "category": ,
                    user: {"id": , "name": , "email": },
                    comments: {"id": , "content": , "rating": , "date": ,
                     "user": {"id": , "name": , "email": }}}}"""
        checking_api_key(key)
        abort_if_news_not_found(news_id)

        session = db_session.create_session()
        news = session.query(News).filter(News.id == news_id).first()
        if news.banned or news.user.banned:
            return jsonify({"Error": {"message": "Эта новость была забанена"}})
        information = {'news': news.to_dict(only=('id', 'name', 'rating', 'content', 'date', "who_likes_it"))}
        user = news.user
        information["news"]["user"] = {"id": user.id, "name": user.name, "email": user.email}
        category = news.category
        information["news"]["category"] = category.name
        comments = news.comments
        information["news"]["comments"] = [{
            "id": comment.id, "content": comment.content, "rating": comment.rating,
            "user": {"id": comment.user_id, "name": comment.user.name, "email": user.email},
            "date": comment.date
        } for comment in comments if not comment.banned and not comment.user.banned]
        return jsonify(information)

    def put(self, news_id, key):
        checking_api_key(key)
        abort_if_news_not_found(news_id)

        args = put_parser.parse_args()

        session = db_session.create_session()
        news = session.query(News).filter(News.id == news_id).first()
        for key, value in args.items():
            if not (value is None):
                if key == "name":
                    news.name = value
                elif key == "rating":
                    news.rating = value
                elif key == "content":
                    news.content = value
                elif key == "category":
                    categories = session.query(Category).all()
                    if value not in list(map(lambda x: x.name, categories)):
                        return jsonify({"Error": {"message": "Такая категория не существует"}})
                    news.category_id = session.query(Category).filter(Category.name == value).first().id
                elif key == "banned":
                    news.banned = value
                elif key == "who_likes_it":
                    news.who_likes_it = value
        session.commit()
        return jsonify({'success': 'OK'})

    def delete(self, news_id, key):
        checking_api_key(key)
        abort_if_news_not_found(news_id)

        session = db_session.create_session()
        news = session.query(News).filter(News.id == news_id).first()
        # удалим все комментарии
        for comment in news.comments:
            session.delete(comment)
        session.delete(news)
        session.commit()
        return jsonify({'success': 'OK'})


post_parser = reqparse.RequestParser()
post_parser.add_argument('name', required=True)
post_parser.add_argument('content', required=True)
post_parser.add_argument('user_id', required=True, type=int)
post_parser.add_argument('category', required=True)


class NewsListResource(Resource):
    def get(self, key):
        """{news: {'id':, 'name':, 'rating':, 'content':, 'date':, "who_likes_it":, "category": ,
                    user: {"id": , "name": , "email": }}}"""
        checking_api_key(key)

        session = db_session.create_session()
        news = session.query(News).all()
        information = []
        for item in news:
            if not item.banned and not item.user.banned:
                inf = item.to_dict(only=('id', 'name', 'rating',
                                         'content', 'user_id', 'date', "who_likes_it"))
                category = item.category
                inf["category"] = category.name
                user = item.user
                inf["user"] = {"id": user.id, "name": user.name, "email": user.email}
                information.append(inf)
        return jsonify({'news': information})

    def post(self, key):
        checking_api_key(key)

        args = post_parser.parse_args()
        abort_if_user_not_found(args['user_id'])

        session = db_session.create_session()
        categories = session.query(Category).all()
        if args['category'] is None or args['category'] not in list(map(lambda x: x.name, categories)):
            return jsonify({"Error": {"message": "Такая категория не существует"}})
        news = News()
        news.name = args['name']
        news.content = args['content']
        news.user_id = args['user_id']
        news.category_id = session.query(Category).filter(Category.name == args["category"]).first().id
        session.add(news)
        session.commit()
        return jsonify({'success': 'OK'})
