from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class RestorePassword(FlaskForm):
    email = EmailField("Почта", validators=[DataRequired()])
    to_email = EmailField("Почта на которую отправить пароль", validators=[DataRequired()])
    secret_word = StringField('Секретное слово', validators=[DataRequired()])
    submit = SubmitField("Восстановить")
