import os


class PATHS:
    """Paths (constants) to any resources in the project."""

    APPLICATION_ROOT_PATH = os.getenv("APPLICATION_ROOT_PATH", "./")
    VAR_PATH = os.getenv("VAR_PATH", "/tmp/")

    RESOURCES = APPLICATION_ROOT_PATH + "res/"
    DATASETS = RESOURCES + "datasets/"

    DATABASE_SCHEMA = RESOURCES + "schema.sql"
    DATABASE_DEFAULT_DUMP = RESOURCES + "dump.sql"
    DATABASE = VAR_PATH + "database_ctb.db"
