"""
User handling utilities.
"""

from typing import NamedTuple, Literal
import os

import telegram

from furrit.db.utils import connect, exec_sql_file

DB_MODULE_ROOT = os.path.dirname(__file__)
SCHEMA_PATH = os.path.join(DB_MODULE_ROOT, "schema.sql")


# XXX(mwp): the cost of a single awoo in terms of fines
AWOO_FINE_COST = 350


class UserRow(NamedTuple):
    id: int
    tg_id: int
    tg_first_name: str
    tg_last_name: str | None
    tg_username: str | None
    fines: int
    n_awoo: int
    n_pan: int


def rebuild_tables() -> None:
    """
    Rebuild all Datbase Tables.

    WARNING: Destructive.
    """
    exec_sql_file(SCHEMA_PATH)


def try_get_user_by_tg_username(tg_username: str) -> UserRow | None:
    """
    Try to get a UserRow by the Telegram Username.
    """

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT id, tg_id, tg_first_name, tg_last_name, tg_username, fines, n_awoo, n_pan FROM USERS WHERE tg_username = ? LIMIT 1",
        (tg_username,),
    )
    row: tuple[int, int, str, str | None, str | None, int, int, int] | None = (
        cur.fetchone()
    )

    if row is None:
        return None

    cur.close()
    con.close()

    return UserRow(*row)


def try_get_user_by_tg_id(tg_id: int) -> UserRow | None:
    """
    Try to get a UserRow by their Telegram Identifier.
    """
    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT id, tg_id, tg_first_name, tg_last_name, tg_username, fines, n_awoo, n_pan FROM USERS WHERE tg_id = ? LIMIT 1",
        (tg_id,),
    )
    row: tuple[int, int, str, str | None, str | None, int, int, int] | None = (
        cur.fetchone()
    )

    if row is None:
        return None

    cur.close()
    con.close()

    return UserRow(*row)


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


QUOTE_MAX_LEN = 3584


def try_do_add_quote(
    author_msg: telegram.Message, quoter_msg: telegram.Message
) -> tuple[bool, str | None]:
    """
    Try to add the Quote.

    Returns a tuple - the first element is a success or failure, the second is
    the failure message (if there is one).
    """

    quote = author_msg.text
    assert quote is not None

    author = author_msg.from_user
    assert author is not None

    quoter = quoter_msg.from_user
    assert quoter is not None

    # XXX(mwp): to enforce constraint that a quote be associated with one chat
    # make sure both messages involved come from that same chat
    if author_msg.chat.id != quoter_msg.chat.id:
        return (False, "Quoted message must come from same chat")

    chat_id = author_msg.chat.id

    raw = quote.encode("utf-8")
    if len(raw) > QUOTE_MAX_LEN:
        return (False, "Quote is greater than max length")

    con = connect()
    cur = con.cursor()

    # XXX(mwp): check to see if the message being quoted (the addee) has already
    # been quoted before
    cur.execute("SELECT id FROM QUOTES WHERE author_msg_id = ?", (author_msg.id,))
    res: tuple[int] | None = cur.fetchone()

    if res is not None:
        cur.close()
        con.close()

        return (False, "Message has already been quoted!")

    # XXX(mwp): check to see if the message being quoted has itself been used to
    # quote another thing
    cur.execute("SELECT id FROM QUOTES WHERE quoter_msg_id = ?", (author_msg.id,))
    res = cur.fetchone()

    if res is not None:
        cur.close()
        con.close()

        return (False, "Message has been used to quote another message!")

    cur.execute(
        "INSERT INTO QUOTES (tg_chat_id, author_tg_id, author_msg_sent_at, author_msg_id, quoter_tg_id, quoter_msg_sent_at, quoter_msg_id, quote) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            chat_id,
            author.id,
            author_msg.date.isoformat(),
            author_msg.id,
            quoter.id,
            quoter_msg.date.isoformat(),
            quoter_msg.id,
            quote,
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


def do_forgive_fine(
    tg_id: int, amount: int
) -> tuple[Literal[True], int] | tuple[Literal[False], str]:
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
        return (False, "User does not exist!")

    fines = res[0]
    next_fines = fines - amount

    if next_fines < 0:
        return (False, "Fines would become negative!")

    cur.execute("UPDATE USERS SET fines = fines - ? WHERE tg_id = ?", (amount, tg_id))

    con.commit()
    cur.close()
    con.close()

    return (True, next_fines)


def get_user_fines(uid: int) -> int:
    """
    Fetch a User's Fines.
    """
    con = connect()
    cur = con.cursor()

    cur.execute("SELECT fines FROM USERS WHERE id = ?", (uid,))

    res: tuple[int] | None = cur.fetchone()
    cur.close()
    con.close()

    assert res is not None
    fines = res[0]

    return fines
