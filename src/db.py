# db.py
# Handles opening/closing the SQLite connection.
# I made this a context manager so I don't forget to close the connection
# (learned this the hard way after leaving a bunch of db files locked).

import sqlite3
from pathlib import Path


class DatabaseManager:
    def __init__(self, db_path="frc.db"):
        self.db_path = db_path
        self.connection = None

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        # sqlite doesn't turn foreign keys on by default, so we have to do it
        # every time we connect
        self.connection.execute("PRAGMA foreign_keys = ON;")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection is not None:
            if exc_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
            self.connection.close()
            self.connection = None
        return False

    @property
    def conn(self):
        if self.connection is None:
            raise RuntimeError("not connected yet - use 'with DatabaseManager(...) as db:'")
        return self.connection

    def init_db(self, schema_path):
        # runs schema.sql to set up the tables
        schema_text = Path(schema_path).read_text()
        self.conn.executescript(schema_text)
        self.conn.commit()

    def execute(self, query, params=()):
        return self.conn.execute(query, params)

    def executemany(self, query, params_list):
        return self.conn.executemany(query, params_list)

    def commit(self):
        self.conn.commit()
