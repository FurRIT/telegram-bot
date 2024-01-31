# oh god
import datetime

from .db_utils import *


def rebuild_user_tables():
    exec_sql_file('/app/src/main/FURRIT-BOT/db/users.sql')
    exec_sql_file('/app/src/main/FURRIT-BOT/db/quotes.sql')


def rebuild_quote_tables():
    exec_sql_file('/app/src/main/FURRIT-BOT/db/quotes.sql')


def add_pan_count(uid):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT PAN_COUNT FROM USERS WHERE TELEGRAM_ID = %s", (str(uid),))
    count = cursor.fetchone()[0]
    new_count = count + 1

    cursor.execute("UPDATE USERS SET PAN_COUNT = %s "
                   "WHERE TELEGRAM_ID = %s", (new_count, str(uid)))
    conn.commit()
    conn.close()


def add_current_members(username, uid):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT USERNAME FROM USERS WHERE TELEGRAM_ID = %s", (str(uid),))
    existence = cursor.fetchone()

    if not existence:
        cursor.execute("INSERT INTO USERS (TELEGRAM_ID, USERNAME) VALUES (%s, %s)", (uid, username))
        conn.commit()
        conn.close()
        return 1

    else:
        conn.commit()
        conn.close()
        return 0


def add_quote_db(from_uid, to_uid, quote, chat_id, message_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT TELEGRAM_ID FROM QUOTES WHERE QUOTE = %s", (quote,))
    existence = cursor.fetchone()

    if not existence:
        cursor.execute("INSERT INTO QUOTES (CHAT_ID, MESSAGE_ID, TELEGRAM_ID, AUTHORED_TELEGRAM_ID, DATE_ISSUED, "
                       "QUOTE) VALUES (%s, %s, %s, %s, %s, %s)",
                       (str(chat_id), str(message_id), str(from_uid), str(to_uid), str(datetime.date.today()), quote))
        conn.commit()
        conn.close()
        return 1
    else:
        conn.close()
        return 0


def get_members():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM USERS')
    existence = cursor.fetchall()
    return existence


def get_member_by_user(username):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT telegram_id FROM USERS WHERE username = %s', (username,))
    id = cursor.fetchone()
    return id


def add_fine(id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT AWOO_FINE FROM USERS WHERE TELEGRAM_ID = %s", (str(id),))
    existence = cursor.fetchone()
    if existence:
        cursor.execute("UPDATE USERS SET AWOO_FINE = AWOO_FINE + {} WHERE TELEGRAM_ID = '{}'".format(350, str(id)))
        conn.commit()
        conn.close()
        return 1
    else:
        conn.commit()
        conn.close()
        return 0


def remove_fine(amt, id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT AWOO_FINE FROM USERS WHERE TELEGRAM_ID = %s", (str(id),))
    existence = cursor.fetchone()
    if existence:
        cursor.execute("UPDATE USERS SET AWOO_FINE = AWOO_FINE - {} WHERE TELEGRAM_ID = '{}'".format(amt, str(id)))
        conn.commit()
        conn.close()
        return 1
    else:
        conn.commit()
        conn.close()
        return 0


def get_quotes():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM QUOTES')
    existence = cursor.fetchall()
    return existence
