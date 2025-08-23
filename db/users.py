# oh god
import logging
import datetime

from db.utils import connect, exec_sql_file


def rebuild_user_tables():
    exec_sql_file("/app/src/main/FURRIT-BOT/db/users.sql")
    exec_sql_file("/app/src/main/FURRIT-BOT/db/quotes.sql")


def rebuild_quote_tables():
    exec_sql_file("/app/src/main/FURRIT-BOT/db/quotes.sql")


def add_pan_count(uid):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(f"""SELECT PAN_COUNT FROM USERS WHERE TELEGRAM_ID = "{uid}" """)
    count = cursor.fetchone()[0]
    new_count = count + 1

    cursor.execute(
        f"""UPDATE USERS SET PAN_COUNT = {new_count} 
                   WHERE TELEGRAM_ID = "{uid}" """
    )
    conn.commit()
    conn.close()


def add_current_members(username, uid, fname, lname):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(f"""SELECT USERNAME FROM USERS WHERE TELEGRAM_ID = {str(uid)}""")
    existence = cursor.fetchone()

    if not existence:
        cursor.execute(
            f"""INSERT INTO USERS VALUES ("{uid}","{fname}","{lname}","{username}",0,0)"""
        )
        conn.commit()
        conn.close()
        return 1

    else:
        conn.commit()
        conn.close()
        return 0


def add_quote_db(from_uid, to_uid, quote):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(f"""SELECT TELEGRAM_ID FROM QUOTES WHERE QUOTE = "{quote}" """)
    existence = cursor.fetchone()

    if not existence:
        cursor.execute(
            f"""INSERT INTO QUOTES VALUES ({to_uid}, "{quote}",{datetime.date.today()}, {from_uid}) """
        )
        conn.commit()
        conn.close()
        return 1
    else:
        conn.close()
        return 0


def get_members():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM USERS")
    existence = cursor.fetchall()
    return existence


def add_fines(uid, fine):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(f"""SELECT AWOO_FINE FROM USERS WHERE TELEGRAM_ID = {str(uid)} """)
    logging.info(fine)
    existence = cursor.fetchone()
    if existence:
        cursor.execute(
            f"UPDATE USERS SET AWOO_FINE = AWOO_FINE + %s WHERE TELEGRAM_ID = %s",
            (
                int(fine),
                str(uid),
            ),
        )
        conn.commit()
        conn.close()
        return 1
    else:
        conn.commit()
        conn.close()
        return 0


def add_fine(id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(f"""SELECT AWOO_FINE FROM USERS WHERE TELEGRAM_ID = "{str(id)}" """)
    existence = cursor.fetchone()
    if existence:
        cursor.execute(
            f"""UPDATE USERS SET AWOO_FINE = AWOO_FINE + {350} WHERE TELEGRAM_ID = "{str(id)}" """
        )
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
    cursor.execute(f"SELECT AWOO_FINE FROM USERS WHERE TELEGRAM_ID = {str(id)}")
    existence = cursor.fetchone()
    if existence:
        cursor.execute(
            "UPDATE USERS SET AWOO_FINE = AWOO_FINE - {} WHERE TELEGRAM_ID = '{}'".format(
                amt, str(id)
            )
        )
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
    cursor.execute("SELECT * FROM QUOTES")
    existence = cursor.fetchall()
    return existence
