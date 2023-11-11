# oh god
from .db_utils import *


def rebuild_tables():
    exec_sql_file('/app/src/main/FURRIT-BOT/db/users.sql')


def add_pan_count(uid):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT PAN_COUNT FROM USERS WHERE TELEGRAM_ID = %s", (str(uid),))
    count = cursor.fetchone()[0]
    new_count = count + 1

    cursor.execute("UPDATE USERS SET PAN_COUNT = %s "
                   "WHERE TELEGRAM_ID = %s", (new_count, uid))
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


def get_members():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM USERS')
    existence = cursor.fetchall()
    return existence
