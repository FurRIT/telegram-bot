"""
Database Utilities.
"""

import os
import sqlite3

DB_MODULE_ROOT = os.path.dirname(__file__)
SQLITE_DB_PATH = os.path.join(DB_MODULE_ROOT, "..", "data")


def connect() -> sqlite3.Connection:
    """
    Connect to the SQlite Datbase.
    """
    con = sqlite3.connect(SQLITE_DB_PATH)
    return con


def exec_sql_file(path: str) -> None:
    """
    Read and execute an SQL file.
    """
    conn = connect()
    cur = conn.cursor()

    with open(path, "r", encoding="utf-8") as file:
        cur.execute(file.read())

    conn.commit()
    conn.close()
