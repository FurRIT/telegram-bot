"""
User handling utilities.
"""

import os

import telegram

from db.utils import connect, exec_sql_file

DB_MODULE_ROOT = os.path.dirname(__file__)
SCHEMA_PATH = os.path.join(DB_MODULE_ROOT, "schema.sql")


# XXX(mwp): the cost of a single awoo in terms of fines
AWOO_FINE_COST = 350


def rebuild_tables() -> None:
    """
    Rebuild all Datbase Tables.

    WARNING: Destructive.
    """
    exec_sql_file(SCHEMA_PATH)


def add_update_tg_user(user: telegram.User) -> None:
    """
    Add the Telegram user if they are not already registered.

    If the Telegram user is registered, update their details in the database.
    """
    con = connect()
    cur = con.cursor()

    cur.execute("SELECT id FROM USERS WHERE tg_id = ?", (user.id,))
    res: tuple[int] | None = cur.fetchone()

    if res is None:
        cur.execute(
            "INSERT INTO USERS (tg_id, tg_first_name, tg_last_name, tg_username) VALUES (?, ?, ?, ?)",
            (user.id, user.first_name, user.last_name, user.username),
        )
    else:
        uid: int = res[0]
        cur.execute(
            "UPDATE USERS SET tg_first_name = ?, tg_last_name = ?, tg_username = ? WHERE id = ?",
            (user.first_name, user.last_name, user.username, uid),
        )

    con.commit()
    cur.close()
    con.close()


def add_pan_count(tg_id: int) -> None:
    """
    Increment the pan count for a User.
    """
    con = connect()
    cur = con.cursor()

    cur.execute("SELECT n_pan FROM USERS WHERE tg_id = ?", (tg_id,))
    res: tuple[int] | None = cur.fetchone()

    if res is None:
        cur.close()
        con.close()
        return

    n_pan = res[0]
    n_pan += 1

    cur.execute("UPDATE USERS SET n_pan = ? WHERE tg_id = ?", (n_pan, tg_id))

    con.commit()
    con.close()


QUOTE_MAX_LEN = 256


def try_do_add_quote(
    addee_msg: telegram.Message, adder_msg: telegram.Message
) -> tuple[bool, str | None]:
    """
    Try to add the Quote.

    Returns a tuple - the first element is a success or failure, the second is
    the failure message (if there is one).
    """

    quote_txt = addee_msg.text
    assert quote_txt is not None

    addee_user = addee_msg.from_user
    assert addee_user is not None

    adder_user = adder_msg.from_user
    assert adder_user is not None

    raw = quote_txt.encode("utf-8")
    if len(raw) > QUOTE_MAX_LEN:
        return (False, "Quote is greater than max length")

    con = connect()
    cur = con.cursor()

    # XXX(mwp): check to see if the message being quoted (the addee) has already
    # been quoted before
    cur.execute("SELECT id FROM QUOTES WHERE sent_msg = ?", (addee_msg.id,))
    res: tuple[int] | None = cur.fetchone()

    if res is not None:
        cur.close()
        con.close()

        return (False, "Message has already been quoted!")

    # XXX(mwp): check to see if the message being quoted has itself been used to
    # quote another thing
    cur.execute("SELECT id FROM QUOTES WHERE added_msg = ?", (addee_msg.id,))
    res = cur.fetchone()

    if res is not None:
        cur.close()
        con.close()

        return (False, "Message has been used to quote another message!")

    cur.execute(
        "INSERT INTO QUOTES (sent_by, sent_at, sent_msg, added_by, added_at, added_msg, quote) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            addee_user.id,
            addee_msg.date.isoformat(),
            addee_msg.id,
            adder_user.id,
            adder_msg.date.isoformat(),
            adder_msg.id,
            quote_txt,
        ),
    )

    con.commit()
    cur.close()
    con.close()

    return (True, None)


def do_fine_user(tg_id: int, amount: int) -> int | None:
    """
    Add a fine amount to a User.
    """

    con = connect()
    cur = con.cursor()

    cur.execute("SELECT fines FROM USERS WHERE tg_id = ?", (tg_id,))
    res: tuple[int] | None = cur.fetchone()

    if res is None:
        cur.close()
        con.close()
        return None

    cur.execute(
        "UPDATE USERS SET fines = fines + ? WHERE tg_id = ?",
        (
            amount,
            tg_id,
        ),
    )

    con.commit()
    cur.close()
    con.close()

    fines = res[0]

    return fines + amount


def incr_fine_awoo(tg_id: int) -> int | None:
    """
    Increment the awoo count and add fines for a User.

    Returns the fine amount, or None if the User could not be found.
    """
    con = connect()
    cur = con.cursor()

    cur.execute("SELECT fines, n_awoo FROM USERS WHERE tg_id = ?", (tg_id,))
    res: tuple[int, int] | None = cur.fetchone()

    if res is None:
        cur.close()
        con.close()
        return None

    cur.execute(
        f"UPDATE USERS SET fines = fines + {AWOO_FINE_COST}, n_awoo = n_awoo + 1 WHERE tg_id = ?",
        (tg_id,),
    )

    con.commit()
    cur.close()
    con.close()

    fines = res[0]
    return fines + AWOO_FINE_COST


def do_forgive_fine(tg_id: int, amount: int) -> int | None:
    """
    Forgive a fine of some amount.
    """
    con = connect()
    cur = con.cursor()

    cur.execute("SELECT fines FROM USERS WHERE tg_id = ?", (tg_id,))
    res: tuple[int] | None = cur.fetchone()
    if res is None:
        cur.close()
        con.close()
        return None

    cur.execute("UPDATE USERS SET fines = fines - ? WHERE tg_id = ?", (amount, tg_id))

    con.commit()
    cur.close()
    con.close()

    fines = res[0]
    return fines - amount


def get_quotes():
    """
    Get all Quotes.
    """
    con = connect()
    cur = con.cursor()

    cur.execute("SELECT * FROM QUOTES")
    res = cur.fetchall()

    cur.close()
    con.close()

    return res
