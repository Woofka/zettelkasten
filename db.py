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


class Tag:
    def __init__(self, tag_id, user_id, tag_str):
        self.id = tag_id
        self.user_id = user_id
        self.tag_str = tag_str

    def __repr__(self):
        return f'<Tag {self.id}>'

    def __hash__(self):
        return hash((self.id, self.user_id, self.tag_str))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    @staticmethod
    def _get_tag_id(user_id, tag_str, conn_curs=None):
        if conn_curs is None:
            conn = get_db_connection()
            cursor = conn.cursor()
        else:
            conn, cursor = conn_curs

        query = r"select id from user_tags " \
                r"where user_id = %s and tag = %s;"
        cursor.execute(query, (user_id, tag_str))
        result = cursor.fetchone()
        if result is None:
            tag_id = None
        else:
            tag_id = result[0]

        if conn_curs is None:
            cursor.close()
            conn.close()

        return tag_id

    @staticmethod
    def _add_user_tag(user_id, tag_str, conn_curs=None):
        if conn_curs is None:
            conn = get_db_connection()
            cursor = conn.cursor()
        else:
            conn, cursor = conn_curs

        query = r"insert into user_tags (user_id, tag) " \
                r"values (%s, %s) " \
                r"returning id;"
        cursor.execute(query, (user_id, tag_str))
        tag_id = cursor.fetchone()[0]

        if conn_curs is None:
            conn.commit()
            cursor.close()
            conn.close()

        return tag_id

    @staticmethod
    def add_tag(user_id, note_id, tag_str, conn_curs=None):
        if conn_curs is None:
            conn = get_db_connection()
            cursor = conn.cursor()
        else:
            conn, cursor = conn_curs

        tag_id = Tag._get_tag_id(user_id, tag_str, conn_curs=(conn, cursor))
        if tag_id is None:
            tag_id = Tag._add_user_tag(user_id, tag_str, conn_curs=(conn, cursor))

        query = r"insert into note_tags (tag_id, note_id) " \
                r"values (%s, %s);"
        cursor.execute(query, (tag_id, note_id))

        if conn_curs is None:
            conn.commit()
            cursor.close()
            conn.close()

        return Tag(tag_id, user_id, tag_str)

    @staticmethod
    def delete_tag(tag_id, note_id, conn_curs=None):
        if conn_curs is None:
            conn = get_db_connection()
            cursor = conn.cursor()
        else:
            conn, cursor = conn_curs

        query = r"delete from note_tags " \
                r"where tag_id = %s and note_id = %s;"
        cursor.execute(query, (tag_id, note_id))

        # TODO: удалить тег из user_tags, если больше нигде не используется

        if conn_curs is None:
            conn.commit()
            cursor.close()
            conn.close()

    @staticmethod
    def get_note_tags(note_id, conn_curs=None):
        if conn_curs is None:
            conn = get_db_connection()
            cursor = conn.cursor()
        else:
            conn, cursor = conn_curs

        query = r"select tag_id, user_id, tag from note_tags " \
                r"left join user_tags on note_tags.tag_id = user_tags.id " \
                r"where note_id = %s;"
        cursor.execute(query, (note_id,))
        result = cursor.fetchall()
        tags = set()
        for row in result:
            tags.add(Tag(row[0], row[1], row[2]))

        if conn_curs is None:
            cursor.close()
            conn.close()

        return tags


class Note:
    def __init__(self, note_id, user_id, title, text, dt_added, dt_edited, tags):
        self.id = note_id
        self.user_id = user_id
        self.title = title
        self.text = text
        self.dt_added = dt_added
        self.dt_edited = dt_edited
        self.tags = tags

    def __repr__(self):
        return f'<Note {self.id}>'

    @staticmethod
    def add_note(user_id, title, text, tags_str):
        conn = get_db_connection()
        cursor = conn.cursor()

        query = r"insert into notes (user_id, title, text, dt_added) " \
                r"values (%s, %s, %s, %s) " \
                r"returning id;"
        dt_added = datetime.now()
        cursor.execute(query, (user_id, title, text, dt_added))
        note_id = cursor.fetchone()[0]

        tags = set()
        for tag_str in tags_str:
            tag = Tag.add_tag(user_id, note_id, tag_str, (conn, cursor))
            tags.add(tag)

        conn.commit()
        cursor.close()
        conn.close()

        return Note(note_id, user_id, title, text, dt_added, None, tags)

    @staticmethod
    def update_note(note, new_title, new_text, new_tags_str_list):
        query_set_part = ''
        set_values = []
        if note.title != new_title:
            query_set_part += r'title = %s, '
            set_values.append(new_title)
        if note.text != new_text:
            query_set_part += r'text = %s, '
            set_values.append(new_text)

        tags_updated = sorted([t.tag_str for t in note.tags]) != sorted(new_tags_str_list)

        if len(set_values) == 0 and not tags_updated:
            return None

        dt_edited = datetime.now()

        conn = get_db_connection()
        cursor = conn.cursor()

        query = r"update notes set " + query_set_part + \
                r"dt_edited = %s where id = %s;"
        set_values.append(dt_edited)
        set_values.append(note.id)
        cursor.execute(query, set_values)

        if tags_updated:
            curr_tags_str = {t.tag_str for t in note.tags}
            new_tags_str = set(new_tags_str_list)
            tags_str_to_delete = curr_tags_str.difference(new_tags_str)
            tags_to_delete = [t for t in note.tags if t.tag_str in tags_str_to_delete]
            tags_str_to_add = new_tags_str.difference(curr_tags_str)

            if len(tags_str_to_delete) > 0:
                for tag_to_delete in tags_to_delete:
                    Tag.delete_tag(tag_to_delete.id, note.id, (conn, cursor))
                    note.tags.remove(tag_to_delete)

            if len(tags_str_to_add) > 0:
                for tags_str_to_add in tags_str_to_add:
                    tag = Tag.add_tag(note.user_id, note.id, tags_str_to_add, (conn, cursor))
                    note.tags.add(tag)

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
            tags = Tag.get_note_tags(note_id, conn_curs=(conn, cursor))
            note = Note(result[0], result[1], result[2], result[3], result[4], result[5], tags)

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
            tags = Tag.get_note_tags(row[0], conn_curs=(conn, cursor))
            note = Note(row[0], row[1], row[2], row[3], row[4], row[5], tags)
            notes.append(note)

        cursor.close()
        conn.close()

        return notes


# print(User.is_email_used('test@test.ru'))
# print(User.add_user('test3@test.ru', '1234'))
# print(User.get_user_by_id(5))
# print(User.authenticate_user('test3@test.ru', '1234'))

def pn(n):
    print(n.id, n.title, n.text, n.dt_added, n.dt_edited)
    if len(n.tags) == 0:
        print('  no tags')
    else:
        for t in n.tags:
            print(' ', t.id, t.user_id, t.tag_str)


notes = Note.get_user_notes(2)
for i in notes:
    pn(i)
    print()

# test_user = User(5, 'test@test.ru', None, None)
# note = Note.add_note(test_user.id, f'Added2', f'Text', ['tag3', 'tag4'])
# pn(note)
# note = Note.update_note(note, note.title, note.text, ['tag3', 'tag2', 'tag5'])
# pn(note)



# for i in range(5):
#     Note.add_note(test_user.id, f'Title{i}', f'Text{i}')

# note = Note.get_note(2)
# print(note.id, note.title, note.text, note.dt_added, note.dt_edited)
# Note.update_note(note, None, None)
# print(note.id, note.title, note.text, note.dt_added, note.dt_edited)

# Note.delete_note(2)

# notes = Note.get_user_notes(3)
# for n in notes:
#     print(n, n.tags)

# tags = {Tag(1, 1, 'a'), Tag(2, 1, 'b'), Tag(3, 1, 'c')}
# ids = sorted([t.tag_str for t in tags])
# ids2 = sorted([t.tag_str for t in tags])
