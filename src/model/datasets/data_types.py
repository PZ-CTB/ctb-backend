from dataclasses import dataclass


@dataclass
class BaseData:
    """Base dataclass for model data."""

    @classmethod
    def fields(cls) -> list[str]:
        """Field names defined in derived dataclasses."""
        return list(cls.__annotations__.keys())


@dataclass
class UnparsedBaseData(BaseData):
    """Unparsed data base dataclass."""

    ...


@dataclass
class InvalidData(UnparsedBaseData):
    """Unparsed data with invalid format."""

    pass


@dataclass
class ArticleData(UnparsedBaseData):
    """Unparsed single article's data."""

    id: int
    title: str
    publication: str
    author: str
    date: str
    year: int
    month: int
    url: str
    content: str


@dataclass
class TweetData(UnparsedBaseData):
    """Unparsed single tweet's data."""

    id: int
    datetime: str
    query: str
    author: str
    content: str


@dataclass
class MlData(BaseData):
    """The final data which is used in an AI model."""

    year: int
    month: int
    day: int
    hour: int
    minute: int
    content: str
