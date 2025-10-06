#!/usr/bin/env python3
"""
Import Parsed Data.
"""

from typing import TypedDict, Iterable, TypeGuard, TypeAlias, cast
import sys
import enum
import pathlib
import sqlite3
import os.path
import argparse
import importlib.resources

import furrit.db

import ijson


class RawUser(TypedDict):
    """
    Entry in `users.json` file.

    See also `dump_user` in tg-remake repository.
    """

    id: int
    first_name: str
    last_name: str | None
    username: str | None


RawUserRow: TypeAlias = tuple[int, str, str | None, str | None]


class RawLegacyQuote(TypedDict):
    """
    A legacy Quote standardized from imported CSV files.
    """

    tg_chat_id: int
    author_tg_id: int
    author_msg_sent_at: str
    author_msg_id: int
    quoter_tg_id: int
    quote: str
    nsfw: int


RawLegacyQuoteRow: TypeAlias = tuple[int, int, str, int, int, str]


def _raw_legacy_quote_to_row(quote: RawLegacyQuote) -> RawLegacyQuoteRow:
    return (
        quote["tg_chat_id"],
        quote["author_tg_id"],
        quote["author_msg_sent_at"],
        quote["author_msg_id"],
        quote["quoter_tg_id"],
        quote["quote"],
    )


class RawRemakeQuote(TypedDict):
    """
    A re-parsed Quote from tg-remake.

    See `scan_messages_added_quotes` command.
    """

    tg_chat_id: int
    author_tg_id: int
    author_msg_sent_at: str
    author_msg_id: int
    quoter_tg_id: int
    quoter_msg_sent_at: str
    quoter_msg_id: int
    quote: str


RawRemakeQuoteRow: TypeAlias = tuple[int, int, str, int, int, str, int, str]


def _raw_remake_quote_to_row(quote: RawRemakeQuote) -> RawRemakeQuoteRow:
    return (
        quote["tg_chat_id"],
        quote["author_tg_id"],
        quote["author_msg_sent_at"],
        quote["author_msg_id"],
        quote["quoter_tg_id"],
        quote["quoter_msg_sent_at"],
        quote["quoter_msg_id"],
        quote["quote"],
    )


def insert_users(con: sqlite3.Connection, users_path: str) -> None:
    """
    Insert all Users from `users.json.`
    """
    cur = con.cursor()

    def _make_row_iterator() -> Iterable[RawUserRow]:
        with open(users_path, "r", encoding="utf-8") as file:
            for thing in ijson.items(file, "item"):
                raw_user = cast(RawUser, thing)

                raw_row = (
                    raw_user["id"],
                    raw_user["first_name"],
                    raw_user["last_name"],
                    raw_user["username"],
                )
                yield raw_row

    row_iterator = _make_row_iterator()

    def first_name_defined(raw_user_row: RawUserRow) -> TypeGuard[RawUserRow]:
        return raw_user_row[1] is not None

    cur.executemany(
        "INSERT INTO USERS (tg_id, tg_first_name, tg_last_name, tg_username) VALUES (?, ?, ?, ?)",
        filter(first_name_defined, row_iterator),
    )

    con.commit()
    cur.close()


@enum.unique
class QuoteKind(enum.Enum):
    """
    Quote Type.
    """

    LEGACY = 0
    REMAKE = 1


_INSERT_STATEMENT: dict[QuoteKind, str] = {
    QuoteKind.LEGACY: "INSERT INTO QUOTES (tg_chat_id, author_tg_id, author_msg_sent_at, author_msg_id, quoter_tg_id, quote) VALUES (?, ?, ?, ?, ?, ?)",
    QuoteKind.REMAKE: "INSERT INTO QUOTES (tg_chat_id, author_tg_id, author_msg_sent_at, author_msg_id, quoter_tg_id, quoter_msg_sent_at, quoter_msg_id, quote) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
}

SomeQuote: TypeAlias = RawLegacyQuote | RawRemakeQuote


def insert_quotes(con: sqlite3.Connection, quotes_path: str) -> None:
    """
    Insert all Quotes from `quotes.json.`
    """

    with open(quotes_path, "r", encoding="utf-8") as file:
        for thing in ijson.items(file, "item"):
            some_quote = cast(SomeQuote, thing)

            if "quoter_msg_id" in some_quote:
                remake_quote = cast(RawRemakeQuote, some_quote)
                row = _raw_remake_quote_to_row(remake_quote)

                kind = QuoteKind.REMAKE
            else:
                legacy_quote = cast(RawLegacyQuote, some_quote)
                assert isinstance(legacy_quote["nsfw"], int)

                if legacy_quote["nsfw"] == 1:
                    continue

                row = _raw_legacy_quote_to_row(legacy_quote)
                kind = QuoteKind.LEGACY

            cur = con.cursor()

            stmt = _INSERT_STATEMENT[kind]
            cur.execute(stmt, row)

            con.commit()
            cur.close()


def main() -> None:
    """
    Parse Arguments.
    """
    parser = argparse.ArgumentParser(prog="import")
    parser.add_argument(
        "-u",
        "--users",
        default="users.json",
        help="users file (default %(default)s)",
    )
    parser.add_argument(
        "-q",
        "--quotes",
        default="quotes.json",
        help="quotes file (default %(default)s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="database.db",
        help="output database (default %(default)s)",
    )
    args = parser.parse_args()

    if os.path.exists(args.output):
        print("error: output file already exists", file=sys.stderr)
        sys.exit(1)

    pathlib.Path(args.output).touch()

    sql_schema_path = importlib.resources.files(furrit.db).joinpath("schema.sql")

    con = sqlite3.connect(args.output)
    cur = con.cursor()

    with sql_schema_path.open("r", encoding="utf-8") as file:
        cur.executescript(file.read())

    con.commit()
    cur.close()

    insert_users(con, args.users)
    insert_quotes(con, args.quotes)


if __name__ == "__main__":
    main()
