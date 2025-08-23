#!/usr/bin/env python3
"""
Insert Quotes from a CSV.
"""

import os
import csv
import sqlite3
import argparse

BIN_ROOT = os.path.dirname(__file__)
REPO_ROOT = os.path.join(BIN_ROOT, "..")

DEFAULT_DB_PATH = os.path.relpath(os.path.join(REPO_ROOT, "database.db"))


def main() -> None:
    """
    Parse Arguments; Insert Quotes.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("quotefile", help="quotes file path (default %(default)s)")
    parser.add_argument(
        "-s",
        "--sqlite",
        help="sqlite file path (default %(default)s)",
        default=DEFAULT_DB_PATH,
    )
    args = parser.parse_args()

    connection = sqlite3.connect(args.sqlite)
    cursor = connection.cursor()

    with open(args.quotes, "r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=";")

        for row in reader:
            print(row)
            text = row[0]
            chat_id = row[1]
            _message_id = row[2]
            authored_by = row[3]
            quoted_by = row[4]
            date = str(row[5])
            nsfw = row[6]

            cursor.execute(
                """
                INSERT INTO quotes (Quote_Author, quote, date_issued, issued_by_id, Chat_ID, NSFW)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (authored_by, text, date, quoted_by, chat_id, nsfw),
            )

    connection.commit()


if __name__ == "__main__":
    main()
