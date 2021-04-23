from data import db_session
from data.categories import Category

standard_categories = ["Всякая всячина", "Юмор", "Познавательный контент",
                       "Наука", "Здоровье", "Автомобили"]


def main():
    db_sess = db_session.create_session()
    categories_in_db = list(map(lambda x: x.name, db_sess.query(Category).all()))
    for category in standard_categories:
        if category not in categories_in_db:
            _category = Category()
            _category.name = category
            db_sess.add(_category)
    db_sess.commit()


if __name__ == '__main__':
    main()
