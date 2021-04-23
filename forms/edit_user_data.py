from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import EmailField


class EditUserData(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField('Изменить')
