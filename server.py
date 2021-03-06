# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Message, Mail
from flask_restful import Api

from requests import get, post, delete, put
from api import users, news, comments
from data.news import News

from forms.user import RegisterForm
from forms.login import LoginForm
from forms.create_post import CreatePost
from forms.post import CommentForm
from forms.block_it import BlockItPost
from forms.edit_user_data import EditUserData
from forms.edit_user_password import EditUserPassword
from forms.restore_password import RestorePassword

import datetime
import smtplib

from data import db_session
from data.users import User
from data import main
from data.main import standard_categories

import json

app = Flask(__name__)
api = Api(app)

with open("settings.json") as file:
    data = json.load(file)
    for key, value in data["basic_settings"].items():
        app.config[key] = value
    api_key = data["api"]["api_key"]

mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)

scheduledatelist = ['02-08', '03-20', '04-12', '05-01', '09-08', '11-26']
data_with_holiday = {
    '02-08': 'День Российской науки',
    '03-20': 'День Земли',
    '04-12': 'День космонавтики',
    '05-01': 'Праздник весны и труда',
    '09-08': 'Международный день грамотности',
    '11-26': 'Всемирный день информации'
}

# для списка объектов
api.add_resource(users.UserListResource, '/api/users/<string:key>')
api.add_resource(news.NewsListResource, '/api/news/<string:key>')
api.add_resource(comments.CommentListResource, '/api/comments/<string:key>')

# для одного объекта
api.add_resource(users.UserResource, '/api/users/<int:user_id>&<string:key>')
api.add_resource(news.NewsResource, '/api/news/<int:news_id>&<string:key>')
api.add_resource(comments.CommentResource, '/api/comments/<int:comment_id>&<string:key>')

# Адреса api
api_news = "http://localhost:8080/api/news"
api_users = "http://localhost:8080/api/users"
api_comments = "http://localhost:8080/api/comments"


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
@app.route('/index')
@app.route('/index/<string:category>')
def index(category=None):
    # Получаем список новостей
    list_with_posts = get(f"{api_news}/{api_key}").json()["news"]
    # Сортируем по категории
    if not (category is None) and category in standard_categories:
        list_with_posts = [_news for _news in list_with_posts if _news["category"] == category]
    # Выбираем 10 новостей с самыми высокими рейтингами
    top_10_news = sorted(list_with_posts, key=lambda x: x["rating"], reverse=True)[:10]

    today = str(datetime.date.today())
    list_time_to_view = list(
        filter(lambda date: date[:2] == today[5:7] and date[3:] > today[8:] or date[:2] > today[5:7],
               list(reversed(scheduledatelist))))
    time_before = min(list_time_to_view,
                      key=lambda s: datetime.datetime.strptime(s, "%m-%d").date() - datetime.date.today())
    time_before = today[:4] + '-' + time_before, data_with_holiday[time_before]
    return render_template("index.html",
                           list_with_posts=list_with_posts,
                           time_before=time_before,
                           styles='index',
                           categories=standard_categories,
                           top=top_10_news)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.banned:
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            return render_template("login.html", message="Данный пользователь заблокирован",
                                   form=form, title='ComNetwork | Авторизация')
        return render_template("login.html", message="Неправильный логин или пароль",
                               form=form, title='ComNetwork | Авторизация')
    return render_template("login.html", form=form, title='ComNetwork | Авторизация')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Делаем запрос в api для добавления нового пользователя
        post_request = post(f"{api_users}/{api_key}", json={
            "name": form.name.data,
            "email": form.email.data,
            "about": form.about.data,
            "password": form.password.data,
            "secret_word": form.secret_word.data
        }).json()
        if "success" in post_request:
            return redirect('/')
        else:
            return render_template("register.html", form=form,
                                   message=post_request["Error"]["message"])
    return render_template("register.html", form=form, title='ComNetwork | Регистрация')


@app.route("/create_post", methods=["POST", "GET"])
@login_required
def create_post():
    form = CreatePost()
    if form.validate_on_submit():
        # Делаем запрос в api для добавления нового поста
        post_request = post(f"{api_news}/{api_key}", json={
            "name": form.title.data,
            "content": form.text.data,
            "category": form.category.data,
            "user_id": current_user.id
        }).json()
        if "success" in post_request:
            return redirect('/')
        else:
            # В случае если api вернул ошибку отправляем сообщение из api на шаблон
            return render_template("сreate_post.html", form=form,
                                   message=post_request["Error"]["message"],
                                   categories=", ".join(standard_categories))
    else:
        return render_template("сreate_post.html", form=form,
                               title="ComNetwork | Создание нового поста",
                               categories=", ".join(standard_categories))


@app.route('/edit_post/<int:news_id>', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    form = CreatePost()
    if request.method == "GET":
        _request = get(f"{api_news}/{news_id}&{api_key}").json()
        if "Error" not in _request:
            _request = _request["news"]
            form.title.data = _request["name"]
            form.text.data = _request["content"]
            form.category.data = _request["category"]
        else:
            abort(404)
    if form.validate_on_submit():
        _request = get(f"{api_news}/{news_id}&{api_key}").json()["news"]
        if _request["user"]["id"] == current_user.id:
            put(f"{api_news}/{news_id}&{api_key}", json={
                "name": form.title.data, "content": form.text.data, "category": form.category.data
            }).json()
            return redirect('/')
        else:
            abort(404)
    return render_template("сreate_post.html", form=form,
                           title="ComNetwork | Редактирование поста",
                           categories=", ".join(standard_categories))


@app.route('/post_delete/<int:news_id>', methods=['GET', 'POST'])
@login_required
def post_delete(news_id):
    delete(f"{api_news}/{news_id}&{api_key}").json()
    return redirect('/')


@app.route("/save_offers", methods=['post', 'get'])
def save_offers():
    if request.method == 'POST':
        msg = Message("Recommendations", sender=app.config['MAIL_USERNAME'], recipients=[app.config['MAIL_USERNAME']])
        msg.body = f"<h1>{request.form.get('message')}</h1>"
        mail.send(msg)
    return redirect('/index')


# функция которая проверяет, понравилась ли пользователю данная новость (пост = новость)
def check_like(news_id, user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if user:
        _news = db_sess.query(News).filter(News.id == news_id).first()
        if _news:
            return str(user_id) in _news.who_likes_it
    return abort(404)


# Функция которая добавляет/убирает очки рейтинга для данного поста и его владельца
# Функции like и check_like работают с бд напрямую, т.к это быстрее, чем через api
@app.route("/like/<int:news_id>&<int:user_id>")
@login_required
def like(news_id, user_id):
    r = check_like(news_id, user_id)
    db_sess = db_session.create_session()
    _news = db_sess.query(News).filter(News.id == news_id).first()
    list_of_people_who_liked_it = list(_news.who_likes_it.split(", "))
    if r:
        del list_of_people_who_liked_it[user_id]
        _news.rating -= 1
        _news.user.rating -= 1
    else:
        list_of_people_who_liked_it += [str(user_id)]
        _news.rating += 1
        _news.user.rating += 1
    _news.who_likes_it = ", ".join(list_of_people_who_liked_it)
    db_sess.commit()
    return redirect(f"/post/{news_id}")


# Функция показывающая пост и комментарии написанные к нему
@app.route("/post/<int:id_post>", methods=['GET', 'POST'])
def __post(id_post):
    form = CommentForm()
    if form.validate_on_submit():
        post(f"{api_comments}/{api_key}", json={
            "content": form.text.data, "user_id": current_user.id, "news_id": id_post
        }).json()

        return redirect(f'/post/{id_post}')

    _post = get(f"{api_news}/{id_post}&{api_key}").json()["news"]

    if current_user.is_authenticated:
        return render_template("post.html", form=form, title="ComNetwork",
                               post=_post, like=check_like(id_post, current_user.id))
    return render_template("post.html", form=form, title="ComNetwork",
                           post=_post)


# Блокирует пользователя/новость/комментарий, но нужно иметь уровень доступа 2 и выше (1-ый ур.д)
@app.route('/block_it/<string:_type>&<int:_id>', methods=['GET', 'POST'])
@login_required
def block_it(_type, _id):
    if current_user.is_authenticated and (current_user.access_level == 1 or current_user.access_level == 2):
        form = BlockItPost()
        if form.validate_on_submit():
            _types = {}
            if _type == "news":
                _types["api"] = api_news
                _types["email"] = get(f"{api_news}/{_id}&{api_key}").json()["news"]["user"]["email"]
                _types["text"] = "Здравствуйте, ваш пост был заблокирован по следующей причине:"
            elif _type == "user":
                _types["api"] = api_users
                _types["email"] = get(f"{api_users}/{_id}&{api_key}").json()["user"]["email"]
                _types["text"] = "Здравствуйте, ваш аккаунт был заблокирован по следующей причине:"
            elif _type == "comment":
                _types["api"] = api_comments
                _types["email"] = get(f"{api_comments}/{_id}&{api_key}").json()["comment"]["user"]["email"]
                _types["text"] = "Здравствуйте, ваше сообщение было заблокирована по следующей причине:"
            else:
                abort(400)

            # Отправляем письмо на почту владельца с причиной блокировки
            text = f'{_types["text"]}\n' \
                   f'{form.text.data}\n' \
                   f'Если вы не согласны с блокировкой, напишите ответное письмо.'

            smtp_host = 'smtp.mail.ru'
            _login, password = data["basic_settings"]["MAIL_USERNAME"], data["basic_settings"]["MAIL_PASSWORD"]

            s = smtplib.SMTP(smtp_host, 25, timeout=10)
            s.set_debuglevel(1)
            try:
                s.starttls()
                s.login(_login, password)
                s.sendmail(_login, [_types["email"]], text.encode("utf-8"))
            finally:
                s.quit()

            put(f"{_types['api']}/{_id}&{api_key}", json={"banned": True})

            return redirect("/")
        return render_template("block_it.html", form=form, title="ComNetwork")


@app.route('/user/<int:_id>')
@login_required
def _user(_id):
    user = get(f"{api_users}/{_id}&{api_key}").json()
    if "Error" not in user:
        return render_template("user.html", title="ComNetwork", user=user["user"])
    else:
        return render_template("user.html", title="ComNetwork", user={"banned": True})


@app.route("/edit_user_data/<int:_id>", methods=['GET', 'POST'])
@login_required
def edit_user_data(_id):
    user = get(f"{api_users}/{_id}&{api_key}").json()
    if "Error" not in user:
        user = user["user"]
        if current_user.is_authenticated and current_user.id == _id:
            form = EditUserData()
            if request.method == "POST":

                _request = put(f"{api_users}/{_id}&{api_key}", json={
                    "email": form.email.data,
                    "about": form.about.data if form.about.data else ""
                }).json()

                if "Error" in _request:
                    return render_template("edit_user_data.html", title="ComNetwork", form=form,
                                           user=user, message=_request["Error"]["message"])
                return redirect(f"/user/{_id}")
            elif request.method == "GET":
                form.email.data = user["email"]
                form.about.data = user["about"]
            return render_template("edit_user_data.html", title="ComNetwork", user=user, form=form)
        else:
            abort(401)
    else:
        abort(400)


@app.route("/edit_user_password/<int:_id>", methods=['GET', 'POST'])
@login_required
def edit_user_password(_id):
    user = get(f"{api_users}/{_id}&{api_key}").json()
    if "Error" not in user:
        user = user["user"]
        if current_user.is_authenticated and current_user.id == _id:
            form = EditUserPassword()
            if request.method == "POST":

                _request = put(f"{api_users}/{_id}&{api_key}", json={
                    "password": form.new_password.data,
                    "last_password": form.last_password.data
                }).json()

                if "Error" in _request:
                    return render_template("/edit_user_password.html", title="ComNetwork", form=form,
                                           user=user, message=_request["Error"]["message"])
                return redirect(f"/user/{_id}")
            return render_template("edit_user_password.html", title="ComNetwork", form=form, user=user)
        else:
            abort(401)
    else:
        abort(400)


def create_password():
    password = []
    password += list(set([chr(i) for i in range(65, 91)]))[:5]
    password += list(set([chr(i) for i in range(97, 123)]))[:5]
    password += list(set([chr(i) for i in range(48, 58)]))[:5]
    return "".join(set(password))


@app.route("/restore_password", methods=['GET', "POST"])
def restore_password():
    form = RestorePassword()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user is None:
            return render_template("restore_password.html", title="ComNetwork",
                                   form=form, message="Пользователь с таким email не зарегистрирован")
        if user.banned:
            return render_template("restore_password.html", title="ComNetwork",
                                   form=form, message="Пользователь с таким email заблокирован")
        if form.secret_word.data != user.secret_word:
            return render_template("restore_password.html", title="ComNetwork",
                                   form=form, message="Секретное слово неверное")
        password = create_password()
        user.set_password(password)
        db_sess.commit()

        text = f"Ваш новый пароль - {password}"

        _login, password = data["basic_settings"]["MAIL_USERNAME"], data["basic_settings"]["MAIL_PASSWORD"]

        smtp_host = 'smtp.mail.ru'
        s = smtplib.SMTP(smtp_host, 25, timeout=10)
        s.set_debuglevel(1)
        try:
            s.starttls()
            s.login(_login, password)
            s.sendmail(_login, [form.to_email.data], text.encode("utf-8"))
        finally:
            s.quit()
        return redirect("/")
    return render_template("restore_password.html", form=form, title='ComNetwork | Регистрация')


if __name__ == "__main__":
    db_session.global_init("db/collective_blog.db")
    main.main()  # Загружаем в бд стандартную информацию
    app.run(port=8080, host='127.0.0.1')
