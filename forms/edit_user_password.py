from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired


class EditUserPassword(FlaskForm):
    last_password = PasswordField('Прошлый пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired()])
    submit = SubmitField('Изменить')
