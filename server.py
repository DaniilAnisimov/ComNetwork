from flask import Flask, render_template, request, redirect, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Message, Mail

from forms.user import RegisterForm
from forms.login import LoginForm
from forms.create_post import CreatePost
from forms.post import CommentForm
import datetime

from data import db_session
from data.users import User
from data.news import News
from data.comments import Comment

import json

from re import *

app = Flask(__name__)

with open("settings.json") as file:
    data = json.load(file)
    for key, value in data.items():
        app.config[key] = value

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


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    db_sess = db_session.create_session()
    list_with_posts_from_db = db_sess.query(News).all()
    today = str(datetime.date.today())
    list_time_to_view = list(
        filter(lambda date: date[:2] == today[5:7] and date[3:] > today[8:] or date[:2] > today[5:7],
               list(reversed(scheduledatelist))))
    time_before = min(list_time_to_view,
                      key=lambda s: datetime.datetime.strptime(s, "%m-%d").date() - datetime.date.today())
    time_before = today[:4] + '-' + time_before, data_with_holiday[time_before]
    return render_template("index.html",
                           list_with_posts=list_with_posts_from_db,
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
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.name == form.name.data).first():
            return render_template("register.html", form=form, message="Имя пользователя занято")
        pattern = compile("(^|\s)[-a-z0-9_.]+@([-a-z0-9]+\.)+[a-z]{2,6}(\s|$)")
        if not pattern.match(form.email.data):
            return render_template('register.html', form=form, message="Почта не действительна")
        if db_sess.query(User).filter(User.address == form.email.data).first():
            return render_template('register.html', form=form,
                                   message="Пользователь с этой почтой уже зарегистрирован")
        if form.password.data != form.password_again.data:
            return render_template("register.html", form=form, message="Пароли не совпадают")
        user = User()
        user.name = form.name.data
        user.email = form.email.data
        user.about = form.about.data
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/')
    return render_template("register.html", form=form, title='ComNetwork | Регистрация')


@app.route("/create_post", methods=["POST", "GET"])
def create_post():
    form = CreatePost()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.name = form.title.data
        news.content = form.text.data
        news.tags = form.tags.data
        news.user_id = current_user.id
        db_sess.add(news)
        db_sess.commit()
        return redirect('/')
    else:
        return render_template("сreate_post.html", form=form, title="ComNetwork | Создание нового поста")


@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = CreatePost()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.user_id == current_user.id).first()
        if news:
            form.title.data = news.name
            form.text.data = news.content
            form.tags.data = news.tags
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.user_id == current_user.id).first()
        if news:
            news.name = form.title.data
            news.content = form.text.data
            news.tags = form.tags.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template("сreate_post.html", form=form, title="ComNetwork | Редактирование поста")


@app.route('/post_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def post_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id, News.user_id == current_user.id).first()
    if news:
        for comment in news.comments:
            db_sess.delete(comment)
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route("/save_offers", methods=['post', 'get'])
def save_offers():
    if request.method == 'POST':
        msg = Message("Recommendations", sender=app.config['MAIL_USERNAME'], recipients=[app.config['MAIL_USERNAME']])
        msg.body = f"<h1>{request.form.get('message')}</h1>"
        mail.send(msg)
    return redirect('/index')


@app.route("/post/<int:id_post>", methods=['GET', 'POST'])
def post(id_post):
    form = CommentForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        comment = Comment()
        comment.content = form.text.data
        comment.user_id = current_user.id
        comment.news_id = id_post
        db_sess.add(comment)
        db_sess.commit()
        return redirect(f'/post/{id_post}')
    db_sess = db_session.create_session()
    _post = db_sess.query(News).filter(News.id == id_post).first()
    if _post is None:
        abort(404)
    return render_template("post.html", form=form, title="ComNetwork", post=_post)


if __name__ == "__main__":
    db_session.global_init("db/collective_blog.db")
    app.run(port=8080, host='127.0.0.1')
