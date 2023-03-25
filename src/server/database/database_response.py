from typing import Any

from . import Message


class DatabaseResponse:
    """Class holding a response of the DatabaseProvider along with the data from cursors.

    If the DatabaseResponse.message is 'OK', the query has been executed successfully.
    Otherwise, there has been an internal error.

    On 'SELECT' queries, DatabaseResponse.data field is expected to hold some meaningful
    information. On 'INSERT" queries, usually this field remains empty. It is also expectable to be
    empty on an error.
    """

    def __init__(self, message: Message, data: list[Any] = []):
        """Initialize an instance of DatabaseResponse."""
        self._message = message
        self._data = data

    @property
    def message(self) -> Message:
        """Read-only property to the message field."""
        return self._message

    @property
    def data(self) -> list[Any]:
        """Read-only property to the data field."""
        return self._data
