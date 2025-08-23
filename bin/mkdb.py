#!/usr/bin/env python3
"""
Create a local SQLite Database.
"""

import sys
import pathlib
import sqlite3
import os.path
import argparse

BIN_DIR_ROOT = os.path.dirname(__file__)
DEFAULT_DB_PATH = os.path.relpath(os.path.join(BIN_DIR_ROOT, "..", "database.db"))

DB_MOD_ROOT = os.path.join(BIN_DIR_ROOT, "..", "db")

USERS_SCHEMA_PATH = os.path.join(DB_MOD_ROOT, "users.sql")
QUOTES_SCHEMA_PATH = os.path.join(DB_MOD_ROOT, "quotes.sql")


def _execute(conn: sqlite3.Connection, path: str) -> None:
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()

    conn.executescript(text)


def main() -> None:
    """
    Parse Arguments and Initialize Database.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--force", help="override existing file", action="store_true"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="output database file (default %(default)s)",
        default=DEFAULT_DB_PATH,
    )
    args = parser.parse_args()

    if os.path.exists(args.output) and not args.force:
        print(
            f"""error: output file {args.output} already exists
       use --force to override anyways"""
        )
        sys.exit(1)

    pathlib.Path(args.output).touch(exist_ok=args.force)
    conn = sqlite3.connect(args.output)

    _execute(conn, USERS_SCHEMA_PATH)
    _execute(conn, QUOTES_SCHEMA_PATH)

    conn.commit()


if __name__ == "__main__":
    main()
