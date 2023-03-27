import os
import sqlite3

from . import PATHS


def get_database_connection() -> sqlite3.Connection:
    """Return connected transaction tunnel to the database."""
    return sqlite3.connect(PATHS.DATABASE)


def _init_database() -> None:
    """Create SQLite3 database and insert some default historic data."""
    if not os.path.exists(PATHS.DATABASE):
        connection = get_database_connection()
        cursor = connection.cursor()
        with open(file=PATHS.DATABASE_SCHEMA, encoding="utf-8") as f:
            cursor.executescript(f.read())
        with open(file=PATHS.DATABASE_DEFAULT_DUMP, encoding="utf-8") as f:
            cursor.executescript(f.read())
        cursor.close()
        connection.commit()
        connection.close()


_init_database()
