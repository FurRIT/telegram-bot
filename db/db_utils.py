"""
Database Utilities.
"""

import os
import sqlite3

DB_MODULE_ROOT = os.path.dirname(__file__)
SQLITE_DB_PATH = os.path.join(DB_MODULE_ROOT, "..", "data")


def connect():
    con = sqlite3.connect(SQLITE_DB_PATH)
    return con

def exec_sql_file(path):
    full_path = path
    conn = connect()
    cur = conn.cursor()
    with open(full_path, "r") as file:
        cur.execute(file.read())
    conn.commit()
    conn.close()


def exec_get_one(sql, args={}):
    conn = connect()
    cur = conn.cursor()
    cur.execute(sql, args)
    one = cur.fetchone()
    conn.close()
    return one


def exec_get_all(sql, args={}):
    conn = connect()
    cur = conn.cursor()
    cur.execute(sql, args)
    # https://www.psycopg.org/docs/cursor.html#cursor.fetchall

    list_of_tuples = cur.fetchall()
    conn.close()
    return list_of_tuples


def exec_commit(sql, args={}):
    conn = connect()
    cur = conn.cursor()
    result = cur.execute(sql, args)
    conn.commit()
    conn.close()
    return result
