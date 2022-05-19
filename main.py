from urllib.parse import urlparse, urljoin
from flask import Flask, render_template, flash, redirect, url_for, request, abort
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from db import User


app = Flask(__name__)
app.secret_key = b'Some secret key'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Войдите, чтобы просматривать данную страницу'


class RegisterForm(FlaskForm):
    email = StringField('Эл. почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    # TODO: confirm password
    # password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = StringField('Эл. почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    rememberme = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    email = None
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        if User.is_email_used(email):
            flash('Данная почта уже используется')
            email = None
        else:
            user = User.add_user(email, password)
            form.email.data = ''
            form.password.data = ''
    # TODO: else (if not valid)

    return render_template('register.html', form=form, email=email)


@app.route('/login', methods=['GET', 'POST'])
def login():
    email = None
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.authenticate_user(email, password)
        if user is None:
            flash('Почта или пароль введены неправильно. Попробуйте снова')
            email = None
        else:
            login_user(user, remember=form.rememberme.data)

            next_page = request.args.get('next')
            if not is_safe_url(next_page):
                return abort(400)

            return redirect(next_page or url_for('index'))
    # TODO: else (if not valid)

    return render_template('login.html', form=form, email=email)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/account')
@login_required
def account():
    return render_template('account.html')


app.run('0.0.0.0', 80, True)
