from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    # если пользователь залогинился
    user_from_db = {'nickname': 'Саня'}  # данные о залогиненном пользователе отправятся на представление
    return render_template("index.html", user=user_from_db, is_login='true')

    # если пользователь не залогинился
    return render_template("index.html", is_login='false')


@app.route('/login')
def login():
    return "login"


@app.route('/logout')
def logout():
    return "logout"


@app.route("/register")
def register():
    return 'register'


if __name__ == "__main__":
    app.run(port=8080, host='127.0.0.1')
