import sqlite3
import os

from . import PATHS


def getDatabaseConnection():
    """Return new connection to database."""
    return sqlite3.connect(PATHS.DATABASE)


def __initDatabase__():
    """Create new database if it does not exist."""
    if not os.path.exists(PATHS.DATABASE):
        connection = getDatabaseConnection()
        cursor = connection.cursor()
        with open(PATHS.DATABASE_SCHEMA) as f:
            cursor.executescript(f.read())
        with open(PATHS.DATABASE_DEFAULT_DUMP) as f:
            cursor.executescript(f.read())
        cursor.close()
        connection.commit()
        connection.close()


__initDatabase__()
