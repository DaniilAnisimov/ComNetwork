from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, login_user, login_required, logout_user

from forms.user import RegisterForm
from forms.login import LoginForm

from main import main

from data import db_session
from data.users import User

from re import *


app = Flask(__name__)
app.config["SECRET_KEY"] = "123"  # in json
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    user_from_db = {'nickname': 'Саня'}   # данные о залогиненном пользователе отправятся на представление
    list_with_posts_from_db = {"ультрафиолетовое излучение": "λ < 380нм",
                             "Инфракрасное излучение": "λ > 760нм",
                             "Гамма излучение": "λ = 2 * 10^-10нм и прочее описание",
                             "Рентгеновское излучение": 'Рентгеновское излучение - '
                                                        'электромагнитные волны с '
                                                        'длиной волны от 100 до 10^-3 нм'}   # Словарь постов из бд

    # если пользователь залогинился
    return render_template("index.html", user=user_from_db, list_with_posts=list_with_posts_from_db, is_login='true')
    # если пользователь не залогинился
    return render_template("index.html", list_of_posts=list_of_posts_from_db, is_login='false')


@app.route('/login', methods=["GET", "POST"])
def login():
    user_from_db = {'nickname': 'Саня'}  # данные о залогиненном пользователе отправятся на представление
    list_with_posts_from_db = {"ультрафиолетовое излучение": "λ < 380нм",
                               "Инфракрасное излучение": "λ > 760нм",
                               "Гамма излучение": "λ = 2 * 10^-10нм и прочее описание",
                               "Рентгеновское излучение": 'Рентгеновское излучение - '
                                                          'электромагнитные волны с '
                                                          'длиной волны от 100 до 10^-3 нм'}  # Словарь постов из бд

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.address == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template("login.html", message="Неправильный логин или пароль",
                               form=form, user=user_from_db, list_with_posts=list_with_posts_from_db, is_login='true')
    return render_template("login.html", form=form, user=user_from_db, list_with_posts=list_with_posts_from_db, is_login='true')


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
            return render_template('register.html', form=form, message="Пользователь с этой почтой уже зарегистрирован")
        if form.password.data != form.password_again.data:
            return render_template("register.html", form=form, message="Пароли не совпадают")
        user = User(name=form.name.data,
                    address=form.email.data,
                    about=form.about.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/index')
    return render_template("register.html", form=form)


@app.route("/create_post")
def create_post():
    return 'create-post'


@app.route("/save_offers", methods=['post', 'get'])
def save_offers():
    if request.method == 'POST':
        print(request.form.get('message'))   # Предложения с футера, потом будем где-нибудь сохранять

    return "Ваше предложение принято"


if __name__ == "__main__":
    main()
    app.run(port=8080, host='127.0.0.1')
