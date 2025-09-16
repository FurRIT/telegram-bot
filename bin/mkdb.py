#!/usr/bin/env python3
"""
Create a local SQLite Database.
"""

import sys
import pathlib
import sqlite3
import os.path
import argparse
import importlib.resources

import furrit.db

BIN_DIR_ROOT = os.path.dirname(__file__)
REPO_ROOT = os.path.join(BIN_DIR_ROOT, "..")

DEFAULT_DB_PATH = os.path.relpath(os.path.join(REPO_ROOT, "database.db"))
SCHEMA_PATH = os.path.join(REPO_ROOT, "schema.sql")


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
    schema_txt = importlib.resources.read_text(  # pylint: disable=deprecated-method
        furrit.db, "schema.sql"
    )

    if os.path.exists(args.output) and not args.force:
        print(
            f"""error: output file {args.output} already exists
       use --force to override anyways"""
        )
        sys.exit(1)

    pathlib.Path(args.output).touch(exist_ok=args.force)
    conn = sqlite3.connect(args.output)

    conn.executescript(schema_txt)
    conn.commit()


if __name__ == "__main__":
    main()
