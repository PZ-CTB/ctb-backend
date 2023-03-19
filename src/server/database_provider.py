import os
import sqlite3

from . import PATHS


def getDatabaseConnection() -> sqlite3.Connection:
    """Return connected transaction tunnel to the database."""
    return sqlite3.connect(PATHS.DATABASE)


def __initDatabase__() -> None:
    """Create SQLite3 database and insert some default historic data."""
    if not os.path.exists(PATHS.DATABASE):
        connection = getDatabaseConnection()
        cursor = connection.cursor()
        with open(file=PATHS.DATABASE_SCHEMA, encoding="utf-8") as f:
            cursor.executescript(f.read())
        with open(file=PATHS.DATABASE_DEFAULT_DUMP, encoding="utf-8") as f:
            cursor.executescript(f.read())
        cursor.close()
        connection.commit()
        connection.close()


__initDatabase__()
