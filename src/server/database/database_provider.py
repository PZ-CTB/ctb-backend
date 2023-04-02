from contextlib import contextmanager
from typing import Generator

import psycopg

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
    connection: psycopg.Connection = None  # type: ignore
    db_name: str = "doeqyyge"
    db_user: str = "doeqyyge"
    db_password: str = "sc_3pV9L4dezgJzWWh5wZMtJBhCiBvcS"
    db_hostname: str = "snuffleupagus.db.elephantsql.com"
    db_connection_timeout: int = 30
    # database_source: str = PATHS.DATABASE

    @classmethod
    def initialize(cls) -> None:
        """Initialize connection to the database."""
        # db_needs_setup: bool = False
        # if not os.path.exists(cls.database_source):
        #     db_needs_setup = True

        result: Message = cls._connect_to_database()
        if result is not Message.OK:
            print(f"WARNING: cannot connect to a file database: {result}")
            # print("INFO: connecting to in-memory database as fallback")
            # cls.database_source = ":memory:"
            # result = cls._connect_to_database()
            # if result is not Message.OK:
            #     raise RuntimeError(f"Can't connect to in-memory database: {result}")

        # if db_needs_setup:
        #     cls._fill_database()

    @classmethod
    @contextmanager
    def handler(cls) -> Generator[DatabaseHandler, None, None]:
        """Interface that allows safe query execution in the database.

        Yields:
            DatabaseHandler: Handler consisting of cursor and query execution status (Message).

        """
        # with cls._try_get_cursor() as cursor:
        handler: DatabaseHandler = DatabaseHandler(None, Message.OK)
        try:
            cursor: psycopg.Cursor = cls.connection.cursor()
            handler._cursor = cursor  # pylint: disable=W0212
            yield handler
        except psycopg.IntegrityError as err:
            print(f"ERROR: {err}")
            cls.connection.rollback()
            handler.message = Message.DATABASE_INTEGRITY_ERROR
        except psycopg.ProgrammingError as err:
            print(f"ERROR: {err}")
            cls.connection.rollback()
            handler.message = Message.INVALID_SQL_QUERY
        except psycopg.DataError as err:
            print(f"ERROR: {err}")
            cls.connection.rollback()
            handler.message = Message.INVALID_SQL_QUERY
        except psycopg.InternalError as err:
            print(f"ERROR: {err}")
            cls.connection.rollback()
            handler.message = Message.INTERNAL_DATABASE_ERROR
        except psycopg.NotSupportedError as err:
            print(f"ERROR: {err}")
            cls.connection.rollback()
            handler.message = Message.UNSUPPORTED_OPERATION
        except psycopg.errors.PipelineAborted as err:
            print(f"ERROR: {err}")
            handler.message = Message.NO_CONNECTION
        except psycopg.Error as err:
            print(f"ERROR: {err}")
            cls.connection.rollback()
            handler.message = Message.UNKNOWN_ERROR
        else:
            cls.connection.commit()
            handler.message = Message.OK

    # @classmethod
    # @contextmanager
    # def _try_get_cursor(cls) -> Generator[Optional[psycopg.Cursor], None, None]:
    #     cursor: Optional[psycopg.Cursor] = None
    #     try:
    #         cursor = cls.connection.cursor()
    #         yield cursor
    #     except psycopg.Error as err:
    #         print(f"ERROR: {err}")
    #         cls.connection.rollback()
    #         yield None
    #     else:
    #         cls.connection.commit()
    #     finally:
    #         if cursor is not None:
    #             print("DEBUG: closing sqlite3.Cursor")
    #             cursor.close()
    #             print("DEBUG: committing sqlite3 changes")

    @classmethod
    def _connect_to_database(cls) -> Message:
        try:
            # print(f"INFO: {cls.database_source=}")
            cls.connection = psycopg.connect(
                conninfo=f"dbname={cls.db_name} "
                f"user={cls.db_user} "
                f"host={cls.db_hostname} "
                f"password={cls.db_password} "
                f"connect_timeout={cls.db_connection_timeout}"
            )
        except psycopg.errors.ConnectionTimeout as err:
            print(f"ERROR: can't connect to the database: {err}")
            return Message.NO_CONNECTION
        except psycopg.Error as err:
            print(f"ERROR: {err}")
            return Message.UNKNOWN_ERROR

        return Message.OK

    # @classmethod
    # def _fill_database(cls) -> None:
    #     with cls._try_get_cursor() as cursor:
    #         if cursor is not None:
    #             with open(file=PATHS.DATABASE_SCHEMA, encoding="utf-8") as f:
    #                 cursor.executescript(f.read())
    #             with open(file=PATHS.DATABASE_DEFAULT_DUMP, encoding="utf-8") as f:
    #                 cursor.executescript(f.read())
