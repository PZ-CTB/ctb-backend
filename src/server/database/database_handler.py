import sqlite3

from . import Message


class DatabaseHandler:
    """Class holding a connected sqlite3.Cursor instance with message about query execution status.

    If the DatabaseResponse.message is 'OK', the query has been executed successfully.
    Otherwise, there has been an internal error.

    The user does not have to worry about cursor commiting changes.
    """

    def __init__(self, cursor: sqlite3.Cursor, message: Message):
        """Initialize the handler with connected cursor and message held by DatabaseProvider.

        Args:
            cursor (sqlite3.Cursor): Cursor of the database directly responsible for queries.
            message (Message): Status of the executed queries.

        """
        self._cursor: sqlite3.Cursor = cursor
        self._message: Message = message

    @property
    def success(self) -> bool:
        """Getter returning success status of the query.

        Returns:
            bool: True if query succeeded, False otherwise.

        """
        return self._message is Message.OK

    @property
    def cursor(self) -> sqlite3.Cursor:
        """Getter to cursor directly responsible for queries.

        Returns:
            sqlite3.Cursor: Cursor held by DatabaseProvider.

        """
        print("DEBUG: Getting Handler.cursor")
        return self._cursor

    @property
    def message(self) -> Message:
        """Getter to the status message of the executed query.

        Returns:
            Message: OK if query executed successfully, anything else otherwise.

        """
        return self._message

    @message.setter
    def message(self, msg: Message) -> None:
        """Setter of query status message.

        Args:
            msg (Message): Message instance given by DatabaseProvider.

        """
        self._message = msg
        print(f"DEBUG: query result -- {self._message}")

    def __call__(self) -> sqlite3.Cursor:
        """Magic function allowing to treat Handler as a function.

        Returns:
            sqlite3.Cursor: Connected cursor to the database.

        """
        return self.cursor
