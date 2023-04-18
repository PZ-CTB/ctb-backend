from dataclasses import dataclass
from enum import IntEnum


@dataclass(frozen=True)
class Message(IntEnum):
    """Common results of operations performed on a database."""

    OK = 0
    UNKNOWN_ERROR = 1
    NO_CONNECTION = 2
    DATABASE_INTEGRITY_ERROR = 3
    INVALID_SQL_QUERY = 4
    UNSUPPORTED_OPERATION = 5
    INTERNAL_DATABASE_ERROR = 6

    def __repr__(self) -> str:
        """Display enum variables with their names and values."""
        return f"{self.name}({self.value})"

    def __str__(self) -> str:
        """Convert enum variables with their names and values to string."""
        return f"{self.name}({self.value})"
