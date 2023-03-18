import os

def defaultEnv(key: str, default: str = ""):
    value = os.getenv(key)
    if value is None:
        return default
    return value

class PATHS:

    APPLICATION_ROOT_PATH = defaultEnv("APPLICATION_ROOT_PATH", "./")
    VAR_PATH = defaultEnv("VAR_PATH", "/tmp/")
    
    RESOURCES = APPLICATION_ROOT_PATH + "res/"
    DATASETS = RESOURCES + "datasets/"
    
    DATABASE_SCHEMA = RESOURCES + "schema.sql"
    DATABASE_DEFAULT_DUMP = RESOURCES + "dump.sql"
    DATABASE = VAR_PATH + "database_ctb.db"
    
    CERTIFICATES_PATH = RESOURCES + "cert/"
    CERTIFICATE = CERTIFICATES_PATH + "example.crt"
    CERTIFICATE_KEY = CERTIFICATES_PATH + "example.key"

