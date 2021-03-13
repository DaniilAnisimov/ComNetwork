from flask import Flask
from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = "123"  # in json


def main():
    db_session.global_init("db/collective_blog.db")


if __name__ == '__main__':
    main()
