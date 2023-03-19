import os
import sqlite3

from . import PATHS


def loadDefaultDataToDatabase() -> None:  # noqa: D103
    pass


def initDatabase() -> None:
    """Create SQLite3 database and insert some default historic data."""
    if not os.path.exists(PATHS.DATABASE):
        connection = sqlite3.connect(PATHS.DATABASE)
        cursor = connection.cursor()
        with open(PATHS.DATABASE_SCHEMA, mode="r", encoding="utf-8") as f:
            cursor.executescript(f.read())
        with open(PATHS.DATABASE_DEFAULT_DUMP, mode="r", encoding="utf-8") as f:
            cursor.executescript(f.read())
        cursor.close()
        connection.commit()
        connection.close()


initDatabase()
