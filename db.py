from datetime import datetime

import psycopg2
from flask_login import UserMixin


def get_db_connection():
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        database='zettelkasten',
        user='app',
        password='0000'
    )
    return conn


class User(UserMixin):
    def __init__(self, user_id, email, password_hash, dt_added):
        self.id = user_id
        self.email = email
        self.password_hash = password_hash
        self.dt_added = dt_added

    def __repr__(self):
        return f'<User {self.id}>'

    @staticmethod
    def authenticate_user(email, password):
        conn = get_db_connection()
        cursor = conn.cursor()

        query = r"select id, email, password_hash, dt_added " \
                r"from users " \
                r"where email = %s and password_hash = crypt(%s, password_hash);"
        cursor.execute(query, (email, password))
        result = cursor.fetchone()
        if result is None:
            user = None
        else:
            user = User(result[0], result[1], result[2], result[3])

        cursor.close()
        conn.close()

        return user

    @staticmethod
    def is_email_used(email):
        conn = get_db_connection()
        cursor = conn.cursor()

        query = r"select id from users where email = %s;"
        cursor.execute(query, (email, ))
        result = cursor.fetchone()
        if result is None:
            result = False
        else:
            result = True

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def add_user(email, password):
        conn = get_db_connection()
        cursor = conn.cursor()

        query = r"insert into users (email, password_hash, dt_added) " \
                r"values (%s, crypt(%s, gen_salt('bf')), %s) " \
                r"returning id, password_hash;"
        dt_added = datetime.now()
        cursor.execute(query, (email, password, dt_added))
        user_id, password_hash = cursor.fetchone()

        conn.commit()
        cursor.close()
        conn.close()

        return User(user_id, email, password_hash, dt_added)

    @staticmethod
    def get_user(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()

        query = r"select id, email, password_hash, dt_added from users where id = %s;"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        if result is None:
            user = None
        else:
            user = User(result[0], result[1], result[2], result[3])

        cursor.close()
        conn.close()

        return user


class Note:
    def __init__(self, note_id, user_id, title, text, dt_added, dt_edited):
        self.id = note_id
        self.user_id = user_id
        self.title = title
        self.text = text
        self.dt_added = dt_added
        self.dt_edited = dt_edited

    def __repr__(self):
        return f'<Note {self.id}>'

    @staticmethod
    def add_note(user_id, title, text):
        conn = get_db_connection()
        cursor = conn.cursor()

        query = r"insert into notes (user_id, title, text, dt_added) " \
                r"values (%s, %s, %s, %s) " \
                r"returning id;"
        dt_added = datetime.now()
        cursor.execute(query, (user_id, title, text, dt_added))
        note_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        return Note(note_id, user_id, title, text, dt_added, None)

    @staticmethod
    def update_note(note, new_title, new_text):
        query_set_part = ''
        set_values = []
        if note.title != new_title:
            query_set_part += r'title = %s, '
            set_values.append(new_title)
        if note.text != new_text:
            query_set_part += r'text = %s, '
            set_values.append(new_text)
        if len(set_values) == 0:
            return note

        conn = get_db_connection()
        cursor = conn.cursor()

        query = r"update notes set " + query_set_part + \
                r"dt_edited = %s where id = %s;"
        dt_edited = datetime.now()
        set_values.append(dt_edited)
        set_values.append(note.id)
        cursor.execute(query, set_values)

        conn.commit()
        cursor.close()
        conn.close()

        note.title = new_title
        note.text = new_text
        note.dt_edited = dt_edited

        return note

    @staticmethod
    def delete_note(note_id):
        conn = get_db_connection()
        cursor = conn.cursor()

        query = r"delete from notes " \
                r"where id = %s;"
        cursor.execute(query, (note_id,))

        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def get_note(note_id):
        conn = get_db_connection()
        cursor = conn.cursor()

        query = r"select id, user_id, title, text, dt_added, dt_edited " \
                r"from notes " \
                r"where id = %s;"
        cursor.execute(query, (note_id,))
        result = cursor.fetchone()
        if result is None:
            note = None
        else:
            note = Note(result[0], result[1], result[2], result[3], result[4], result[5])

        cursor.close()
        conn.close()

        return note

    @staticmethod
    def get_user_notes(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()

        query = r"select id, user_id, title, text, dt_added, dt_edited " \
                r"from notes " \
                r"where user_id = %s;"
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        notes = []
        for row in result:
            notes.append(Note(row[0], row[1], row[2], row[3], row[4], row[5]))

        cursor.close()
        conn.close()

        return notes


# print(User.is_email_used('test@test.ru'))
# print(User.add_user('test3@test.ru', '1234'))
# print(User.get_user_by_id(5))
# print(User.authenticate_user('test3@test.ru', '1234'))

# test_user = User(3, 'test@test.ru', None, None)
# for i in range(5):
#     Note.add_note(test_user.id, f'Title{i}', f'Text{i}')

# note = Note.get_note(2)
# print(note.id, note.title, note.text, note.dt_added, note.dt_edited)
# Note.update_note(note, None, None)
# print(note.id, note.title, note.text, note.dt_added, note.dt_edited)

# Note.delete_note(2)

# notes = Note.get_user_notes(3)
# for n in notes:
#     print(n)
