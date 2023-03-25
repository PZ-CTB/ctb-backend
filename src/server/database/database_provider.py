import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

from .. import PATHS
from . import DatabaseResponse, Message


class DatabaseProvider:
    """Interface to SQL database.

    Example usage:
        DatabaseProvider.initialize()  # init database
        age: int = 66
        with DatabaseProvider.query(
            "SELECT name FROM person WHERE age=?", (age,)
        ) as response:
            if response.message is Message.OK:
                name: list[str] = response.data
            else:
                # handle query failure
    """

    connection: sqlite3.Connection = sqlite3.Connection(":memory:")
    database_source: str = ""

    @classmethod
    def initialize(cls) -> None:
        """Initialize connection to the database."""
        cls.database_source = PATHS.DATABASE

        if not os.path.exists(cls.database_source):
            result = cls._create_database()
            if result is Message.NO_CONNECTION:
                print("INFO: connecting to in-memory database as fallback")
                cls.database_source = ":memory:"
                cls._create_database()
        cls._fill_database()

    @classmethod
    @contextmanager
    def query(cls, query: str, params: tuple = ()) -> Generator[DatabaseResponse, None, None]:
        """Interface that allows safe query execution in database.

        Args:
            query (str): Query to be executed in the database.
            params (tuple, optional): Parameters passed to sqlite3 query string. Defaults to ().

        Yields:
            DatabaseResponse: Batch containing query execution status and received data (if any).
        """
        with cls._try_get_cursor() as cursor:
            if cursor is None:
                yield DatabaseResponse(Message.NO_CONNECTION, [])
            else:
                try:
                    print(f"INFO: {query=}, {params=}")
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    data: list = cursor.fetchall()
                    yield DatabaseResponse(Message.OK, data)
                except sqlite3.IntegrityError as err:
                    print(f"ERROR: {err}")
                    yield DatabaseResponse(Message.INVALID_SQL, [])
                except sqlite3.ProgrammingError as err:
                    print(f"ERROR: {err}")
                    yield DatabaseResponse(Message.INVALID_BINDINGS, [])
                except sqlite3.Error as err:
                    print(f"ERROR: {err}")
                    yield DatabaseResponse(Message.UNKNOWN_ERROR, [])
                finally:
                    print(f"INFO: successfully executed a query: '{query}'")

    @classmethod
    @contextmanager
    def _try_get_cursor(cls) -> Generator[Optional[sqlite3.Cursor], None, None]:
        cursor: Optional[sqlite3.Cursor] = None
        try:
            cursor = cls.connection.cursor()
            yield cursor
        except sqlite3.Error as err:
            print(f"ERROR: {err}")
            yield None
        finally:
            if cursor is not None:
                cursor.close()
                cls.connection.commit()

    @classmethod
    def _create_database(cls) -> Message:
        try:
            print(f"INFO: {cls.database_source=}")
            cls.connection = sqlite3.connect(cls.database_source, check_same_thread=False)
        except sqlite3.OperationalError as err:
            print(f"ERROR: can't connect to the database: {err}")
            return Message.NO_CONNECTION
        except sqlite3.Error as err:
            print(f"ERROR: {err}")
            return Message.UNKNOWN_ERROR

        return Message.OK

    @classmethod
    def _fill_database(cls) -> None:
        with cls._try_get_cursor() as cursor:
            if cursor is not None:
                with open(file=PATHS.DATABASE_SCHEMA, encoding="utf-8") as f:
                    cursor.executescript(f.read())
                with open(file=PATHS.DATABASE_DEFAULT_DUMP, encoding="utf-8") as f:
                    cursor.executescript(f.read())
