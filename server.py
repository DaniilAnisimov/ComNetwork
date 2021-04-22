#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Message, Mail
from flask_restful import Api

from requests import get, post, delete, put
from api import users, news, comments

from forms.user import RegisterForm
from forms.login import LoginForm
from forms.create_post import CreatePost
from forms.post import CommentForm
from forms.block_it import BlockItPost
import datetime

import smtplib

from data import db_session
from data.users import User

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
def index():
    list_with_posts = get(f"{api_news}/{api_key}").json()["news"]
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
                           styles='index')


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
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
        post_request = post(f"{api_users}/{api_key}", json={
            "name": form.name.data,
            "email": form.email.data,
            "about": form.about.data,
            "password": form.password.data
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
        post_request = post(f"{api_news}/{api_key}", json={
            "name": form.title.data,
            "content": form.text.data,
            "tags": form.tags.data,
            "user_id": current_user.id
        }).json()
        if "success" in post_request:
            return redirect('/')
        else:
            return render_template("сreate_post.html", form=form,
                                   message=post_request["Error"]["message"])
    else:
        return render_template("сreate_post.html", form=form, title="ComNetwork | Создание нового поста")


@app.route('/edit_post/<int:news_id>', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    form = CreatePost()
    if request.method == "GET":
        _request = get(f"{api_news}/{news_id}&{api_key}").json()["news"]
        if "Error" not in _request:
            form.title.data = _request["name"]
            form.text.data = _request["content"]
            form.tags.data = _request["tags"]
        else:
            abort(404)
    if form.validate_on_submit():
        _request = get(f"{api_news}/{news_id}&{api_key}").json()["news"]
        if _request["user"]["id"] == current_user.id:
            put(f"{api_news}/{news_id}&{api_key}", json={
                "name": form.title.data, "content": form.text.data, "tags": form.tags.data
            }).json()
            return redirect('/')
        else:
            abort(404)
    return render_template("сreate_post.html", form=form, title="ComNetwork | Редактирование поста")


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


@app.route("/post/<int:id_post>", methods=['GET', 'POST'])
def __post(id_post):
    form = CommentForm()
    if form.validate_on_submit():
        post(f"{api_comments}/{api_key}", json={
            "content": form.text.data, "user_id": current_user.id, "news_id": id_post
        }).json()
        return redirect(f'/post/{id_post}')
    _post = get(f"{api_news}/{id_post}&{api_key}").json()["news"]
    return render_template("post.html", form=form, title="ComNetwork", post=_post)


@app.route('/block_it/<string:_type>&<int:_id>', methods=['GET', 'POST'])
@login_required
def block_it(_type, _id):
    if current_user.access_level == 1 or current_user.access_level == 2:
        form = BlockItPost()
        if form.validate_on_submit():
            _types = {}
            if _type == "news":
                _types["api"] = api_news
                _types["email"] = get(f"{api_news}/{_id}&{api_key}").json()["news"]["user"]["email"]
                _types["text"] = "Здравствуйте, ваш пост был заблокирован по следующей причине:"
            elif _types == "user":
                _types["api"] = api_users
                _types["email"] = get(f"{api_users}/{_id}&{api_key}").json()["email"]
                _types["text"] = "Здравствуйте, ваш аккаунт был заблокирован по следующей причине:"
            elif _types == "comment":
                _types["api"] = api_comments
                _types["email"] = get(f"{api_comments}/{_id}&{api_key}").json()["comment"]["user"]["email"]
                _types["text"] = "Здравствуйте, ваше сообщение было заблокирована по следующей причине:"
            else:
                abort(400)

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


if __name__ == "__main__":
    db_session.global_init("db/collective_blog.db")
    app.run(port=8080, host='127.0.0.1')
