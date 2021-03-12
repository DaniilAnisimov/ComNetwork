from flask import Flask, render_template, request

app = Flask(__name__)


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


@app.route("/register")
def register():
    return 'register'


@app.route("/create_post")
def create_post():
    return 'create-post'


@app.route("/save_offers", methods=['post', 'get'])
def save_offers():
    if request.method == 'POST':
        print(request.form.get('message'))   # Предложения с футера, потом будем где-нибудь сохранять

    return "Ваше предложение принято"


if __name__ == "__main__":
    app.run(port=8080, host='127.0.0.1')
