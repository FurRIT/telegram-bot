"""
Quote handling utilities.
"""

from typing import NamedTuple
import re

from db.utils import connect
from db.users import UserRow, try_get_user_by_tg_id, try_get_user_by_tg_username


class QuoteRow(NamedTuple):
    """
    Quote Row.
    """

    id: int
    tg_chat_id: int
    author_tg_id: int
    author_msg_sent_at: str | None
    author_msg_id: int | None
    quoter_tg_id: int
    quoter_msg_sent_at: str
    quoter_msg_id: int | None
    quote: str


def search_quotes(
    query: str, username: str | None = None
) -> tuple[UserRow, QuoteRow] | None:
    """
    Search Quotes table for a Quote.
    """
    extra_where_clause = ""

    if username is not None:
        user_row = try_get_user_by_tg_username(username)
        if user_row is None:
            return None

        extra_where_clause += f" author_tg_id = {user_row.tg_id} AND"

    con = connect()
    cur = con.cursor()

    safe_query = re.escape(query)
    safe_for_like = f"%{safe_query}%"

    cur.execute(
        f"SELECT id, tg_chat_id, author_tg_id, author_msg_sent_at, author_msg_id, quoter_tg_id, quoter_msg_sent_at, quoter_msg_id, quote FROM QUOTES WHERE{extra_where_clause} quote LIKE ? LIMIT 1",
        (safe_for_like,),
    )
    row: (
        tuple[int, int, int, str | None, int | None, int, str, int | None, str] | None
    ) = cur.fetchone()

    cur.close()
    con.close()

    if row is None:
        return None
    quote_row = QuoteRow(*row)

    user_row = try_get_user_by_tg_id(quote_row.author_tg_id)
    if user_row is None:
        return None

    return (user_row, quote_row)


def random_quote() -> tuple[UserRow, QuoteRow] | None:
    """
    Get a random Quote from the database.
    """

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT id, tg_chat_id, author_tg_id, author_msg_sent_at, author_msg_id, quoter_tg_id, quoter_msg_sent_at, quoter_msg_id, quote FROM QUOTES ORDER BY RANDOM() LIMIT 1",
    )

    row: (
        tuple[int, int, int, str | None, int | None, int, str, int | None, str] | None
    ) = cur.fetchone()

    cur.close()
    con.close()

    if row is None:
        return None
    quote_row = QuoteRow(*row)

    user_row = try_get_user_by_tg_id(quote_row.author_tg_id)
    if user_row is None:
        return None

    return (user_row, quote_row)
