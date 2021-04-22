from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField


class BlockItPost(FlaskForm):
    text = TextAreaField("Причина блокировки")
    submit = SubmitField('Отправить')
