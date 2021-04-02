from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField


class CommentForm(FlaskForm):
    text = TextAreaField("Написать комментарий")
    submit = SubmitField("Отправить")
