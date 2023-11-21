# oh god
from .db_utils import *


def rebuild_tables():
    exec_sql_file('/app/src/main/FURRIT-BOT/db/users.sql')


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


def remove_fine(amt,id):
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