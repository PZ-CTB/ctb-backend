import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PATHS:
    """Paths (constants) to any resources in the project."""

    APPLICATION_ROOT_PATH: str = os.getenv("APPLICATION_ROOT_PATH", "./")
    VAR_PATH: str = os.getenv("VAR_PATH", "/tmp/")

    RESOURCES: str = APPLICATION_ROOT_PATH + "res/"
    DATASETS: str = RESOURCES + "datasets/"

    DATABASE_SCHEMA: str = RESOURCES + "schema.sql"
    DATABASE_DEFAULT_DUMP: str = RESOURCES + "dump.sql"
    DATABASE: str = VAR_PATH + "database_ctb.db"


@dataclass(frozen=True)
class CONSTANTS:
    """Variables which are constant through the lifetime of the app."""

    DATABASE_NAME: str = os.getenv("CTB_DB_NAME", "")
    DATABASE_USER: str = os.getenv("CTB_DB_USER", "")
    DATABASE_PASSWORD: str = os.getenv("CTB_DB_PWD", "")
    DATABASE_HOSTNAME: str = os.getenv("CTB_DB_HOST", "")
    DATABASE_CONNECTION_TIMEOUT: int = int(os.getenv("CTB_DB_CONN_TMOUT", 30))


@dataclass(frozen=True)
class QUERIES:
    """All SQL queries used in the project."""

    SELECT_USER_UUID: str = "SELECT uuid FROM users WHERE uuid=%s"
    SELECT_USER_EMAIL: str = "SELECT email FROM users WHERE email=%s"
    SELECT_USER_EMAIL_BY_UUID: str = "SELECT email FROM users WHERE uuid=%s"
    SELECT_USER_LOGIN_DATA_BY_EMAIL: str = (
        "SELECT uuid, email, password_hash FROM users WHERE email=%s"
    )
    SELECT_USER_DATA_BY_UUID: str = "SELECT email, wallet_usd, wallet_btc FROM users WHERE uuid=%s"
    INSERT_USER: str = "INSERT INTO users(uuid, email, password_hash) VALUES (%s, %s, %s)"

    SELECT_REVOKED_TOKEN: str = "SELECT token FROM revoked_tokens WHERE token=%s AND expiry > %s"
    INSERT_REVOKED_TOKEN: str = "INSERT INTO revoked_tokens (token, expiry) VALUES (%s, %s)"

    SELECT_CHART: str = """SELECT date, value FROM exchange_rate_history
                        WHERE date BETWEEN %s and %s
                        ORDER BY date"""
    SELECT_CHART_AGGREGATED: str = """SELECT (DATE_PART('day', date - %s) / %s)::INT as period_number,
                                        MIN(date)::DATE, AVG(value), MIN(value), MAX(value)
                                        FROM exchange_rate_history
                                        WHERE date BETWEEN %s AND %s
                                        GROUP BY period_number
                                        ORDER BY period_number"""

    WALLET_DEPOSIT: str = "UPDATE users SET wallet_usd = wallet_usd + %s WHERE uuid=%s"
