"""
Quote handling utilities.
"""

from typing import NamedTuple
import re
import dataclasses

from src.furrit.db.utils import connect
from src.furrit.db.users import UserRow, try_get_user_by_tg_id, try_get_user_by_tg_username


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
    query: str, tg_chat_id: int, username: str | None = None
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
        f"""
        SELECT
            quotes.id,
            quotes.tg_chat_id,
            quotes.author_tg_id,
            quotes.author_msg_sent_at,
            quotes.author_msg_id,
            quotes.quoter_tg_id,
            quotes.quoter_msg_sent_at,
            quotes.quoter_msg_id,
            quotes.quote,
            users.tg_id
        FROM QUOTES
            JOIN USERS ON quotes.author_tg_id = users.tg_id
        WHERE
            {extra_where_clause}
            tg_chat_id = ? AND
            quote LIKE ?
        ORDER BY
            RANDOM()
        LIMIT 1""",
        (
            tg_chat_id,
            safe_for_like,
        ),
    )
    row: (
        tuple[int, int, int, str | None, int | None, int, str, int | None, str, int]
        | None
    ) = cur.fetchone()

    cur.close()
    con.close()

    if row is None:
        return None

    quote_span: tuple[
        int, int, int, str | None, int | None, int, str, int | None, str
    ] = row[:-1]
    user_span: int = row[-1]

    quote_row = QuoteRow(*quote_span)

    user_row = try_get_user_by_tg_id(user_span)
    if user_row is None:
        return None

    return (user_row, quote_row)


def random_quote(tg_chat_id: int) -> tuple[UserRow, QuoteRow] | None:
    """
    Get a random Quote from the database.
    """

    con = connect()
    cur = con.cursor()

    cur.execute(
        """
        SELECT
            quotes.id,
            quotes.tg_chat_id,
            quotes.author_tg_id,
            quotes.author_msg_sent_at,
            quotes.author_msg_id,
            quotes.quoter_tg_id,
            quotes.quoter_msg_sent_at,
            quotes.quoter_msg_id,
            quotes.quote,
            users.tg_id
        FROM QUOTES
            JOIN USERS on quotes.author_tg_id = users.tg_id
        WHERE
            tg_chat_id = ?
        ORDER BY
            RANDOM()
        LIMIT 1""",
        (tg_chat_id,),
    )

    row: (
        tuple[int, int, int, str | None, int | None, int, str, int | None, str, int]
        | None
    ) = cur.fetchone()

    cur.close()
    con.close()

    if row is None:
        return None

    quote_span: tuple[
        int, int, int, str | None, int | None, int, str, int | None, str
    ] = row[:-1]
    user_span: int = row[-1]
    quote_row = QuoteRow(*quote_span)

    user_row = try_get_user_by_tg_id(user_span)
    if user_row is None:
        return None

    return (user_row, quote_row)


@dataclasses.dataclass(frozen=True)
class QuoteStats:
    """
    Summarized Quote Statistics.
    """

    quote_count: int
    top_quoted: list[tuple[UserRow, int]]
    top_adders: list[tuple[UserRow, int]]


def derive_quote_stats() -> QuoteStats:
    """
    Pull data for a leaderboard of:
    - Total Number Of Quotes
    - Total Times Quoted (most appearances in QUOTES.author_tg_id)
    - Total Quotes Added (most appearances in QUOTES.quoter_tg_id)
    """
    con = connect()
    cur = con.cursor()

    cur.execute("SELECT COUNT(id) FROM QUOTES")
    quote_count_row: tuple[int] | None = cur.fetchone()

    assert quote_count_row is not None
    quote_count, *_ = quote_count_row

    cur.close()
    cur = con.cursor()

    cur.execute(
        "SELECT author_tg_id, COUNT(*) as occurences FROM QUOTES WHERE author_tg_id IN (SELECT tg_id FROM USERS) GROUP BY author_tg_id ORDER BY occurences DESC LIMIT 5"
    )
    top_quoted_rows: list[tuple[int, int]] = cur.fetchall()

    top_quoted = []
    for tg_id, count in top_quoted_rows:
        user = try_get_user_by_tg_id(tg_id)
        assert user is not None

        top_quoted.append((user, count))

    cur.close()
    cur = con.cursor()

    cur.execute(
        "SELECT quoter_tg_id, COUNT(*) as occurences FROM QUOTES WHERE quoter_tg_id IN (SELECT tg_id FROM USERS) GROUP BY quoter_tg_id ORDER BY occurences DESC LIMIT 5"
    )
    top_adders_rows: list[tuple[int, int]] = cur.fetchall()

    top_adders = []
    for tg_id, count in top_adders_rows:
        user = try_get_user_by_tg_id(tg_id)
        assert user is not None

        top_adders.append((user, count))

    cur.close()
    con.close()

    return QuoteStats(quote_count, top_quoted, top_adders)


def derive_user_quote_stats(username: str) -> tuple[UserRow, int, int] | None:
    """
    Pull data for a for a user for:
    - Total Times Quoted
    - Total Quotes Added

    Returns (times_quotes_authored, times_quotes_from_others_added)
    """
    user = try_get_user_by_tg_username(username)
    if user is None:
        return None

    con = connect()
    cur = con.cursor()

    cur.execute("SELECT COUNT(id) FROM QUOTES WHERE author_tg_id = ?", (user.tg_id,))
    author_row: tuple[int] | None = cur.fetchone()

    author_count = author_row[0] if author_row is not None else 0
    cur.close()

    cur = con.cursor()

    cur.execute("SELECT COUNT(id) FROM QUOTES WHERE quoter_tg_id = ?", (user.tg_id,))
    quoter_row: tuple[int] | None = cur.fetchone()

    quoter_count = quoter_row[0] if quoter_row is not None else 0
    cur.close()

    con.close()

    return (user, author_count, quoter_count)
