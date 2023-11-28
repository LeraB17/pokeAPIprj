from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from forms import LoginForm, LoginSecondFactorForm, SignUpForm, ForgotPasswordForm, ChangePasswordForm
from models import db, User
from flask_login import login_required, login_user, logout_user, current_user
import random
import string

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
