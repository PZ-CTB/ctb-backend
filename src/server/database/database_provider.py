import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

from .. import PATHS
from . import DatabaseHandler, Message


class DatabaseProvider:
    """Interface to SQL database.

    There are several steps that happen under the hood which user does not have to worry about:
        - connection to file database (if exists);
        - connection to in-memory database (in case file database failed);
        - safe creation of cursor and transaction (with error handling);
        - execution of queries that we submitted (with error handling);
        - commit of changes in the actual database.

    If an error occurs on one of the queries, any subsequent queries present in the same context
    will not be executed.

        with DatabaseProvider.handler() as handler:
            handler().execute("SELECT name FROM person WHERE age=?", (age,))
            name: list[str] = handler().fetchall()

        if not handler.success:
            # handle query failure
    """

    # predeclaration on the class level
    connection: sqlite3.Connection = sqlite3.Connection(":memory:")
    database_source: str = ""

    @classmethod
    def initialize(cls) -> None:
        """Initialize connection to the database."""
        cls.database_source = PATHS.DATABASE

        db_needs_setup: bool = False
        if not os.path.exists(cls.database_source):
            db_needs_setup = True

        result: Message = cls._connect_to_database()
        if result is not Message.OK:
            print(f"WARNING: cannot connect to a file database: {result}")
            print("INFO: connecting to in-memory database as fallback")
            cls.database_source = ":memory:"
            result = cls._connect_to_database()
            if result is not Message.OK:
                raise RuntimeError(f"Can't connect to in-memory database: {result}")

        if db_needs_setup:
            cls._fill_database()

    @classmethod
    @contextmanager
    def handler(cls) -> Generator[DatabaseHandler, None, None]:
        """Interface that allows safe query execution in the database.

        Yields:
            DatabaseHandler: Handler consisting of cursor and query execution status (Message).

        """
        with cls._try_get_cursor() as cursor:
            if cursor is not None:
                handler: DatabaseHandler = DatabaseHandler(cursor, Message.OK)
                try:
                    yield handler
                except sqlite3.IntegrityError:
                    handler.message = Message.INVALID_SQL
                except sqlite3.ProgrammingError:
                    handler.message = Message.INVALID_BINDINGS
                except sqlite3.Error:
                    handler.message = Message.UNKNOWN_ERROR
                else:
                    handler.message = Message.OK

    @classmethod
    @contextmanager
    def _try_get_cursor(cls) -> Generator[Optional[sqlite3.Cursor], None, None]:
        cursor: Optional[sqlite3.Cursor] = None
        try:
            cursor = cls.connection.cursor()
            yield cursor
        except sqlite3.Error as err:
            print(f"ERROR: sqlite3.Cursor creation -- {err}")
            yield None
        finally:
            if cursor is not None:
                print("DEBUG: closing sqlite3.Cursor")
                cursor.close()
                print("DEBUG: committing sqlite3 changes")
                cls.connection.commit()

    @classmethod
    def _connect_to_database(cls) -> Message:
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
