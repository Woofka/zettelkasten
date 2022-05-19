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


# print(User.is_email_used('test@test.ru'))
# print(User.add_user('test3@test.ru', '1234'))
# print(User.get_user_by_id(5))
# print(User.authenticate_user('test3@test.ru', '1234'))
