#!/usr/bin/env python3
"""
Automatically Migrate Legacy Database Data.
"""

from typing import NamedTuple, Any
import os.path
import sqlite3
import argparse
import datetime

BIN_DIR = os.path.dirname(__file__)
SCHEMA_PATH = os.path.join(BIN_DIR, "..", "db", "schema.sql")


class User(NamedTuple):
    tg_id: int
    tg_first_name: str
    tg_last_name: str | None
    tg_username: str | None
    fines: int
    n_awoo: int
    n_pan: int


class LegacyUser(NamedTuple):
    telegram_id: str | None
    firstName: str | None
    lastName: str | None
    username: str | None
    awoo_fine: int | None
    pan_count: int | None


class Quote(NamedTuple):
    tg_chat_id: int
    author_tg_id: int
    author_msg_sent_at: str | None
    author_msg_id: str | None
    quoter_tg_id: int
    quoter_msg_sent_at: str
    quoter_msg_id: int | None
    quote: str


class LegacyQuote(NamedTuple):
    Quote_Author: str | None
    quote: str | None
    date_issued: str | None
    issued_by_id: str | None
    Chat_ID: str | None
    NSFW: int | None


def _raw_user_to_legacy_user(raw: Any) -> LegacyUser:
    assert isinstance(raw, tuple)
    assert len(raw) == 6

    telegram_id, firstName, lastName, username, awoo_fine, pan_count = raw

    assert telegram_id is None or isinstance(telegram_id, str)
    assert firstName is None or isinstance(firstName, str)
    assert lastName is None or isinstance(lastName, str)
    assert username is None or isinstance(username, str)

    assert awoo_fine is None or isinstance(awoo_fine, int)
    assert pan_count is None or isinstance(pan_count, int)

    if telegram_id is not None and telegram_id == "None":
        telegram_id = None
    if firstName is not None and firstName == "None":
        firstName = None
    if lastName is not None and lastName == "None":
        lastName = None
    if username is not None and username == "None":
        username = None

    return LegacyUser(telegram_id, firstName, lastName, username, awoo_fine, pan_count)


def _legacy_user_to_user(legacy_user: LegacyUser) -> User:
    telegram_id, firstName, lastName, username, awoo_fine, pan_count = legacy_user

    assert telegram_id is not None
    tg_id = int(telegram_id)

    tg_first_name = firstName
    assert tg_first_name is not None

    tg_last_name = lastName
    tg_username = username

    fines = awoo_fine
    if fines is None:
        fines = 0

    n_pan = pan_count
    if n_pan is None:
        n_pan = 0

    return User(tg_id, tg_first_name, tg_last_name, tg_username, fines, 0, n_pan)


def _raw_quote_to_legacy_quote(raw: Any) -> LegacyQuote:
    assert isinstance(raw, tuple)
    assert len(raw) == 6

    Quote_Author, quote, date_issued, issued_by_id, Chat_ID, NSFW = raw

    assert Quote_Author is None or isinstance(Quote_Author, str)
    assert quote is None or isinstance(quote, str)
    assert date_issued is None or isinstance(date_issued, str)
    assert issued_by_id is None or isinstance(issued_by_id, str)
    assert Chat_ID is None or isinstance(Chat_ID, str)
    assert NSFW is None or isinstance(NSFW, int)

    if Quote_Author is not None and Quote_Author == "None":
        Quote_Author = None
    if quote is not None and quote == "None":
        quote = None
    if date_issued is not None and date_issued == "None":
        date_issued = None
    if issued_by_id is not None and issued_by_id == "None":
        issued_by_id = None
    if Chat_ID is not None and Chat_ID == "None":
        Chat_ID = None

    return LegacyQuote(Quote_Author, quote, date_issued, issued_by_id, Chat_ID, NSFW)


MAX_QUOTE_LEN = 3584


def _legacy_quote_to_quote(legacy_quote: LegacyQuote) -> Quote:
    Quote_Author, quote, date_issued, issued_by_id, Chat_ID, _NSFW = legacy_quote

    assert quote is not None
    assert Chat_ID is not None
    assert Quote_Author is not None
    assert issued_by_id is not None
    assert date_issued is not None

    tg_chat_id: int = int(Chat_ID)
    author_tg_id: int = int(Quote_Author)
    author_msg_sent_at = None
    author_msg_id = None

    quoter_tg_id: int = int(issued_by_id)
    quoter_msg_sent_at: str = datetime.datetime.fromisoformat(date_issued).isoformat()
    quoter_msg_id = None

    enc = quote.encode("utf-8")
    assert len(enc) <= MAX_QUOTE_LEN

    return Quote(
        tg_chat_id,
        author_tg_id,
        author_msg_sent_at,
        author_msg_id,
        quoter_tg_id,
        quoter_msg_sent_at,
        quoter_msg_id,
        quote,
    )


def main() -> None:
    """
    Parse Arguments & Write Data.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("legacy", help="legacy database file")
    parser.add_argument(
        "-o",
        "--output",
        help="new database file (default %(default)s)",
        default="database.db",
    )
    args = parser.parse_args()

    con = sqlite3.connect(args.output)
    cur = con.cursor()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        cur.executescript(file.read())

    con.commit()
    cur.close()

    old_con = sqlite3.connect(args.legacy)
    old_cur = old_con.cursor()

    # XXX(mwp): query all users; check that they conform to old invariants, then
    # convert to new version (without id)
    old_cur.execute("SELECT * FROM USERS")

    legacy_users = map(_raw_user_to_legacy_user, old_cur.fetchall())
    users = map(_legacy_user_to_user, legacy_users)

    old_cur.close()

    cur = con.cursor()
    cur.executemany(
        "INSERT INTO USERS (tg_id, tg_first_name, tg_last_name, tg_username, fines, n_awoo, n_pan) VALUES (?, ?, ?, ?, ?, ?, ?)",
        users,
    )

    con.commit()
    cur.close()

    old_cur = old_con.cursor()
    old_cur.execute("SELECT * FROM QUOTES")

    legacy_quotes = map(_raw_quote_to_legacy_quote, old_cur.fetchall())
    quotes = map(_legacy_quote_to_quote, legacy_quotes)

    cur = con.cursor()
    cur.executemany(
        "INSERT INTO QUOTES (tg_chat_id, author_tg_id, author_msg_sent_at, author_msg_id, quoter_tg_id, quoter_msg_sent_at, quoter_msg_id, quote) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        quotes,
    )

    con.commit()
    cur.close()


if __name__ == "__main__":
    main()
