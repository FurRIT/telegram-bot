"""
User handling utilities.
"""

import os
import logging
import datetime

from db.utils import connect, exec_sql_file

DB_MODULE_ROOT = os.path.dirname(__file__)
SCHEMA_PATH = os.path.join(DB_MODULE_ROOT, "schema.sql")


def rebuild_tables() -> None:
    """
    Rebuild all Datbase Tables.

    WARNING: Destructive.
    """
    exec_sql_file(SCHEMA_PATH)


def add_pan_count(uid: int) -> None:
    """
    Increment the pan count for a User.
    """
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


def add_current_members(username: str, uid: int, fname: str, lname: str) -> int:
    """
    Ensure that a User exists in the Database.
    """
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


def add_quote_db(from_uid: int, to_uid: int, quote: str) -> int:
    """
    Add a Quote to the Database.
    """

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
    """
    Get all Users.
    """
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM USERS")
    existence = cursor.fetchall()
    return existence


def add_fines(uid: int, fine: int) -> int:
    """
    Add a fine amount to a User.
    """

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


def add_fine(uid: int) -> int:
    """
    Add a fine of 350 to a User.
    """
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(f"""SELECT AWOO_FINE FROM USERS WHERE TELEGRAM_ID = "{str(uid)}" """)
    existence = cursor.fetchone()
    if existence:
        cursor.execute(
            f"""UPDATE USERS SET AWOO_FINE = AWOO_FINE + {350} WHERE TELEGRAM_ID = "{str(uid)}" """
        )
        conn.commit()
        conn.close()
        return 1
    else:
        conn.commit()
        conn.close()
        return 0


def remove_fine(amt: int, uid: int):
    """
    Forgive a fine of some amount.
    """
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(f"SELECT AWOO_FINE FROM USERS WHERE TELEGRAM_ID = {str(uid)}")
    existence = cursor.fetchone()
    if existence:
        cursor.execute(
            "UPDATE USERS SET AWOO_FINE = AWOO_FINE - {} WHERE TELEGRAM_ID = '{}'".format(
                amt, str(uid)
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
    """
    Get all Quotes.
    """
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM QUOTES")
    existence = cursor.fetchall()
    return existence
