from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, StringField
from wtforms.validators import DataRequired


class CreatePost(FlaskForm):
    title = StringField("Заглавие", validators=[DataRequired()])
    text = TextAreaField("Описание")
    category = StringField("Категория", validators=[DataRequired()])
    submit = SubmitField('Отправить')
