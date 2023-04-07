from contextlib import contextmanager
from typing import Generator

import psycopg

from .. import CONSTANTS
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
    db_name: str = CONSTANTS.DATABASE_NAME
    db_user: str = CONSTANTS.DATABASE_USER
    db_password: str = CONSTANTS.DATABASE_PASSWORD
    db_hostname: str = CONSTANTS.DATABASE_HOSTNAME
    db_connection_timeout: int = CONSTANTS.DATABASE_CONNECTION_TIMEOUT

    @classmethod
    def initialize(cls) -> None:
        """Initialize connection to the database."""
        if "" in [cls.db_name, cls.db_user, cls.db_password, cls.db_hostname]:
            raise EnvironmentError("Cannot launch server due to invalid encironment")

        result: Message = cls._connect_to_database()
        if result is not Message.OK:
            print(f"WARNING: cannot connect to a file database: {result}")

    @classmethod
    @contextmanager
    def handler(cls) -> Generator[DatabaseHandler, None, None]:
        """Interface that allows safe query execution in the database.

        Yields:
            DatabaseHandler: Handler consisting of cursor and query execution status (Message).

        """
        handler: DatabaseHandler = DatabaseHandler(None, Message.OK)  # type: ignore
        try:
            cursor: psycopg.Cursor = cls.connection.cursor()
            handler._cursor = cursor  # pylint: disable=W0212
            yield handler
        except psycopg.Error as err:
            print(f"ERROR: {err}")
            cls.connection.rollback()
            match err:
                case psycopg.IntegrityError():
                    handler.message = Message.DATABASE_INTEGRITY_ERROR
                case psycopg.DataError():
                    handler.message = Message.INVALID_SQL_QUERY
                case psycopg.ProgrammingError():
                    handler.message = Message.INVALID_SQL_QUERY
                case psycopg.InternalError():
                    handler.message = Message.INTERNAL_DATABASE_ERROR
                case psycopg.NotSupportedError():
                    handler.message = Message.UNSUPPORTED_OPERATION
                case psycopg.errors.PipelineAborted():
                    handler.message = Message.NO_CONNECTION
                case psycopg.Error():
                    handler.message = Message.UNKNOWN_ERROR
                case _:
                    handler.message = Message.UNKNOWN_ERROR
        else:
            cls.connection.commit()
            handler.message = Message.OK

    @classmethod
    def _connect_to_database(cls) -> Message:
        try:
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
