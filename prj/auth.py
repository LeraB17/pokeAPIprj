from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from forms import LoginForm, LoginSecondFactorForm, SignUpForm, ForgotPasswordForm, ChangePasswordForm
from models import db, User
from flask_login import login_required, login_user, logout_user, current_user
import random
import string
import requests
from settings import *
from send_email import send_email

auth_app = Blueprint('auth', __name__)

@auth_app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('pokemons'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            code_second = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            print('code_second:', code_second)
            session['code_second'] = {'email': form.email.data, 'code': code_second}
            if IS_CODE_SEND_EMAIL:
                send_email(to_email=user.email,
                           content=code_second,
                           subject='code_second')
            return redirect(url_for('auth.login_second_factor'))
        flash("Invalid username or password", 'error')
        return redirect(url_for('auth.login'))
    return render_template('login.html', form=form)


@auth_app.route('/login/second-factor', methods=['GET', 'POST'])
def login_second_factor():
    if current_user.is_authenticated:
        return redirect(url_for('pokemons'))
    if 'code_second' not in session:
        return redirect(url_for('auth.login'))
    form = LoginSecondFactorForm()
    if form.validate_on_submit():
        if form.code.data == session['code_second']['code']:
            user = User.query.filter_by(email=session['code_second']['email']).first()
            login_user(user)
            return redirect(url_for('pokemons'))
        flash("Uncorrect code", 'error')
        return redirect(url_for('auth.login_second_factor'))
    return render_template('login_second_factor.html', form=form)


@auth_app.route('/login-yandex-id')
def login_yandex_id():
    if current_user.is_authenticated:
        return redirect(url_for('pokemons'))
    return redirect(f"{YANDEX_ID_URL}?response_type=code&client_id={YANDEX_ID_CLIENT_ID}&redirect_uri={YANDEX_ID_CALLBACK_URI}")


@auth_app.route('/login-yandex-id/callback')
def login_yandex_id_callback():
    if current_user.is_authenticated:
        return redirect(url_for('pokemons'))
    # получение access токена
    code = request.args.get('code', None)
    data_request_token = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': YANDEX_ID_CLIENT_ID,
        'client_secret': YANDEX_ID_CLIENT_SECRET,
        'redirect_uri': YANDEX_ID_CALLBACK_URI
    }
    response_token = requests.post(YANDEX_ID_TOKEN_URL, data=data_request_token)

    if response_token.status_code != 200:
        flash('Yandex ID error.', 'error')
        return render_template('login.html', form=LoginForm())

    token_json = response_token.json()

    # получение информации о пользователе Yandex ID
    headers = {'Authorization': f"OAuth {token_json['access_token']}"}
    response = requests.get('https://login.yandex.ru/info?format=json', headers=headers)

    if response.status_code != 200:
        flash('Yandex ID error.', 'error')
        return render_template('login.html', form=LoginForm())

    user_info_json = response.json()
    user_info = {'id': user_info_json.get('id'),
                 'name': user_info_json.get('real_name', None),
                 'email': user_info_json.get('default_email', None)}

    # проверка, если ли такой пользователь
    user = User.query.filter(User.email == user_info['email']).first()
    print(user)
    if user:
        if user.name != user_info['name']:
            user.name = user_info['name']
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash('Failed to update username.', 'error')

        login_user(user)
        return redirect(url_for('pokemons'))
    rnd_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    user = User(name=user_info['name'],
                email=user_info['email'],
                password_hash=rnd_password)
    try:
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('pokemons'))
    except Exception as e:
        db.session.rollback()
        flash('Register error.', 'error')
    return render_template('login.html', form=LoginForm())


@auth_app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('pokemons'))
    form = SignUpForm()
    if form.validate_on_submit():
        try:
            user = User(name=form.name.data,
                        email=form.email.data,
                        password_hash=form.password.data)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('auth.login'))
        except Exception:
            flash('Failed to sign up!', 'error')
            db.session.rollback()
            return render_template('sign_up.html', form=form)
    return render_template('sign_up.html', form=form)


@auth_app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('pokemons'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            print('code:', code)
            session['code'] = {'email': form.email.data, 'code': code}
            if IS_CODE_SEND_EMAIL:
                send_email(to_email=user.email,
                        content=code,
                        subject='code')
            return redirect(url_for('auth.change_password'))
        flash("Account does not exist", 'error')
        return redirect(url_for('auth.forgot_password'))
    return render_template('forgot_password.html', form=form)


@auth_app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if current_user.is_authenticated:
        return redirect(url_for('pokemons'))
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if form.code.data == session['code']['code']:
            try:
                user = User.query.filter_by(email=session['code']['email']).first()
                user.set_password(form.password.data)
                db.session.commit()
                print('change')
                return redirect(url_for('auth.login'))
            except Exception:
                flash('Failed to change password!', 'error')
                db.session.rollback()
                return redirect(url_for('auth.change_password'))
    return render_template('change_password.html', form=form)


@auth_app.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('pokemons'))
