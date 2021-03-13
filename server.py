from flask import Flask, render_template, request, redirect
from forms.user import RegisterForm
from data import db_session
from data.users import User
from re import *
from main import main

app = Flask(__name__)
app.config["SECRET_KEY"] = "123"  # in json


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


@app.route('/login')
def login():
    return "login"


@app.route('/logout')
def logout():
    return "logout"


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
