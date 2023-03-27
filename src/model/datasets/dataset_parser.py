import csv
from datetime import datetime
from typing import Generator, Optional, Type, cast

from . import ArticleData, InvalidData, MlData, TweetData, UnparsedBaseData


class DatasetParser:
    """Read datasets from csv files.

    In order to have a unanimous output data with varying csv formats, any new formats must be added
    to src.datasets.data_types.py file and referenced in both _parse() match-case clause and
    _guess_data_type() types list.

    Example usage:
        parser = DatasetParser("res/datasets/example_articles.csv")
        for idx, content in enumerate(parser.read()):
            print(f"{content.year}, {content.month}, {content.day}")
            if idx > 50: # limit large parsed csv data to 50 rows
                break
    """

    def __init__(self, file_path: str) -> None:
        """Initialize parser and setup reader according to CSV file format."""
        self.file_cursor: int = 0
        self.file_path = file_path
        self.dialect: Optional[Type[csv.Dialect]] = None
        self.field_names: list[str] = []
        self.data_type: Type[UnparsedBaseData] = InvalidData

        self._prepare_reader()
        self._guess_data_type()

    def _prepare_reader(self) -> None:
        with open(self.file_path, encoding="utf-8") as csvfile:
            try:
                self.dialect = csv.Sniffer().sniff(csvfile.read(4096))
            except csv.Error as error:
                print(f"ERROR: {error}")
                self.dialect = None
            finally:
                csvfile.seek(0)

            if self.dialect is not None:
                reader = csv.reader(csvfile, dialect=self.dialect)
            else:
                reader = csv.reader(csvfile)

            self.field_names.extend(next(reader))
            self.field_names.remove("")  # remove a field named: ''
            csvfile.seek(0)

    def _guess_data_type(self) -> None:
        types: list[Type[UnparsedBaseData]] = [ArticleData, TweetData]

        for type_ in types:
            if set(self.field_names) == set(type_.fields()):
                self.data_type = type_
                break

        if self.data_type is InvalidData:
            raise RuntimeError("Unknown data type in DatasetParser")

        print(f"INFO: Assuming {self.data_type.__name__} type")

    def _parse(self, data: UnparsedBaseData) -> MlData:
        match self.data_type.__name__:
            case ArticleData.__name__:
                return MlData(
                    year=cast(ArticleData, data).year,
                    month=cast(ArticleData, data).month,
                    day=int(cast(ArticleData, data).date.split("-")[2]),
                    hour=0,
                    minute=0,
                    content=cast(ArticleData, data).content,
                )
            case TweetData.__name__:
                time = datetime.strptime(cast(TweetData, data).datetime, "%a %b %d %X PDT %Y")
                return MlData(
                    year=time.year,
                    month=time.month,
                    day=time.day,
                    hour=time.hour,
                    minute=time.minute,
                    content=cast(TweetData, data).content,
                )
            case _:
                raise RuntimeError("Tried to parse unknown data type")

    def read(self) -> Generator[MlData, None, None]:
        """Yield one row from CSV without loading whole contents."""
        with open(self.file_path, newline="", encoding="utf-8") as csvfile:
            if self.dialect is not None:
                reader = csv.DictReader(csvfile, dialect=self.dialect)
            else:
                reader = csv.DictReader(csvfile)

            for row in reader:
                row.pop("", "")  # remove a key-value pair where key == ''
                yield self._parse(self.data_type(**row))
