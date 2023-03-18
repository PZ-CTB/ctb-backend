import os

def defaultEnv(key: str, default: str = ""):
    value = os.getenv(key)
    if value is None:
        return default
    return value

class PATHS:

    APPLICATION_ROOT_PATH = defaultEnv("APPLICATION_ROOT_PATH", "./")
    VAR_PATH = defaultEnv("VAR_PATH", "/tmp/")

    DATABASE_SCHEMA = APPLICATION_ROOT_PATH + "res/schema.sql"
    DATABASE = VAR_PATH + "database_ctb.db"
