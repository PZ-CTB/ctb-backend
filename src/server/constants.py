import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PATHS:
    """Paths (constants) to any resources in the project."""

    APPLICATION_ROOT_PATH = os.getenv("APPLICATION_ROOT_PATH", "./")
    VAR_PATH = os.getenv("VAR_PATH", "/tmp/")

    RESOURCES = APPLICATION_ROOT_PATH + "res/"
    DATASETS = RESOURCES + "datasets/"

    DATABASE_SCHEMA = RESOURCES + "schema.sql"
    DATABASE_DEFAULT_DUMP = RESOURCES + "dump.sql"
    DATABASE = VAR_PATH + "database_ctb.db"


@dataclass(frozen=True)
class QUERIES:
    """All SQL queries used in the project."""

    SELECT_USER_UUID = "SELECT uuid FROM users WHERE uuid=%s"
    SELECT_USER_EMAIL = "SELECT email FROM users WHERE email=%s"
    SELECT_USER_EMAIL_BY_UUID = "SELECT email FROM users WHERE uuid=%s"
    SELECT_USER_LOGIN_DATA_BY_EMAIL = "SELECT uuid, email, password_hash FROM users WHERE email=%s"
    SELECT_USER_DATA_BY_UUID = "SELECT email, wallet_usd, wallet_btc FROM users WHERE uuid=%s"
    INSERT_USER = "INSERT INTO users(uuid, email, password_hash) VALUES (%s, %s, %s)"

    SELECT_REVOKED_TOKEN = "SELECT token FROM revoked_tokens WHERE token=%s AND expiry > %s"
    INSERT_REVOKED_TOKEN = "INSERT INTO revoked_tokens (token, expiry) VALUES (%s, %s)"
