from dataclasses import dataclass
from enum import IntEnum


@dataclass(frozen=True)
class Message(IntEnum):
    """Common results of operations performed on a database."""

    OK = 0
    UNKNOWN_ERROR = 1
    NO_CONNECTION = 2
    INVALID_SQL = 3
    INVALID_BINDINGS = 4
    INVALID_THREAD = 5

    def __repr__(self) -> str:
        """Display enum variables with their names and values."""
        return f"{self.name}({self.value})"

    def __str__(self) -> str:
        """Convert enum variables with their names and values to string."""
        return f"{self.name}({self.value})"
