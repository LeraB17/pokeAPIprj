from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, Email, InputRequired, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
    
class LoginSecondFactorForm(FlaskForm):
    code = StringField("Code from email", validators=[DataRequired()])
    submit = SubmitField("Login")
    
class SignUpForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=6, max=20, message="Password must be between 6 and 20 characters long")])
    confirm_password = PasswordField("Password again", validators=[DataRequired(), EqualTo('password', message='Passwords must match'), Length(min=6, max=20, message="Password must be between 6 and 20 characters long")])
    submit = SubmitField("Sign Up")
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email is already registered.')

class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField()
    
class ChangePasswordForm(FlaskForm):
    code = StringField("Code from email", validators=[DataRequired()])
    password = PasswordField("New password", validators=[InputRequired(), Length(min=6, max=20, message="Password must be between 6 and 20 characters long")])
    confirm_password = PasswordField("New password again", validators=[DataRequired(), EqualTo('password', message='Passwords must match'), Length(min=6, max=20, message="Password must be between 6 and 20 characters long")])
    submit = SubmitField()
