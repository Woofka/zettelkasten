from urllib.parse import urlparse, urljoin
from flask import Flask, render_template, flash, redirect, url_for, request, abort
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import markdown
import md_extentions

from db import User, Note, Tag


app = Flask(__name__)
app.secret_key = b'Some secret key'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Войдите, чтобы просматривать данную страницу'


class RegisterForm(FlaskForm):
    email = StringField(validators=[DataRequired(), Email()])
    password = PasswordField(validators=[DataRequired()])
    # TODO: confirm password
    # password2 = PasswordField(validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = StringField(validators=[DataRequired(), Email()])
    password = PasswordField(validators=[DataRequired()])
    rememberme = BooleanField()
    submit = SubmitField('Войти')


class NoteForm(FlaskForm):
    title = StringField()
    text = TextAreaField()
    tags = TextAreaField()
    submit = SubmitField('Создать')


class SearchForm(FlaskForm):
    q = StringField(validators=[DataRequired()])
    submit = SubmitField('Найти')


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
            login_user(user)
            flash('Вы были успешно зарегистированы!')
            return redirect(url_for('index'))
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


@app.route('/notes', methods=['GET'])
@login_required
def notes_page():
    form = SearchForm(request.args)
    search_query = request.args.get('q', None)
    filter_tag_id = request.args.get('t', None)
    if search_query is not None:
        notes = Note.search_notes(current_user.id, search_query)
    elif filter_tag_id is not None:
        try:
            filter_tag_id = int(filter_tag_id)
            notes = Note.get_notes_with_tag(filter_tag_id)
        except ValueError:
            notes = []
    else:
        notes = Note.get_user_notes(current_user.id)

    return render_template('notes.html', notes=notes, form=form)


@app.route('/note/<int:note_local_id>')
@login_required
def note_page(note_local_id):
    note = Note.get_note(current_user.id, note_local_id)
    if note is None:
        flash('Нет заметки с таким идентификатором')
        return abort(404)

    links_from = Note.get_notes_linked_to(current_user.id, note.local_id)
    md = markdown.markdown(note.text, extensions=['fenced_code', md_extentions.StrikeExtension()])

    return render_template('note.html', note=note, md=md, links_from=links_from)


def parse_tags(tags_data):
    tags_data = tags_data.strip().split('\n')
    tags_str = []
    for _str in tags_data:
        _str = _str.strip()
        if len(_str) > 50:
            return None
        if len(_str) > 0:
            tags_str.append(_str)
    return tags_str


@app.route('/add-note', methods=['GET', 'POST'])
@login_required
def add_note():
    form = NoteForm()
    if form.validate_on_submit():
        title = form.title.data
        text = form.text.data
        tags_data = form.tags.data
        tags_str = parse_tags(tags_data)
        if tags_str is None:
            flash('Тег не должен быть длинее 50 символов')
        else:
            note = Note.add_note(current_user.id, title, text, tags_str)
            return redirect(url_for('note_page', note_local_id=note.local_id))
    return render_template('add_note.html', form=form)


@app.route('/edit-note/<int:note_local_id>', methods=['GET', 'POST'])
@login_required
def edit_note(note_local_id):
    note = Note.get_note(current_user.id, note_local_id)
    if note is None:
        flash('Нет заметки с таким идентификатором')
        return abort(404)

    form = NoteForm(
        title=note.title,
        text=note.text,
        tags='\n'.join([t.tag_str for t in note.tags])
    )
    form.submit.label.text = 'Сохранить'

    if form.validate_on_submit():
        title = form.title.data
        text = form.text.data
        tags_data = form.tags.data
        tags_str = parse_tags(tags_data)
        if tags_str is None:
            flash('Тег не должен быть длинее 50 символов')
        else:
            note = Note.update_note(note, title, text, tags_str)
            if note is None:
                flash('Нет изменений. Заметка осталась прежней')
            else:
                flash('Изменения сохранены')
            return redirect(url_for('note_page', note_local_id=note_local_id))
    return render_template('edit_note.html', form=form, note_local_id=note_local_id)


@app.route('/delete-note/<int:note_local_id>', methods=['GET', 'POST'])
@login_required
def delete_note(note_local_id):
    note = Note.get_note(current_user.id, note_local_id)
    if note is None:
        flash('Нет заметки с таким идентификатором')
        return abort(404)

    Note.delete_note(note.id)
    flash('Заметка успешно удалена')
    return redirect(url_for('notes_page'))


@app.route('/tags')
@login_required
def tags_page():
    tags = Tag.get_user_tags(current_user.id)
    return render_template('tags.html', tags=tags)


app.run('0.0.0.0', 80, True)
