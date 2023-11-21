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


def add_fine(int: id):
    conn = connect()
    cursor = conn.cursor()
    print("IT GOT TO THE ADD FINE PART")
    # cursor.execute("SELECT USERNAME FROM USERS WHERE TELEGRAM_ID = %s", (str(uid),))
    sql = '''UPDATE USERS SET awoo_fine = awoo_fine + 350 WHERE telegram_id = 'id' '''

    try:
        cursor.execute(sql)
        conn.commit()
    except:
        conn.rollback()

    conn.close()
    return 1


