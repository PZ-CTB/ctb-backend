
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password_hash TEXT,
    wallet_usd FLOAT NOT NULL DEFAULT 0.0,
    wallet_btc FLOAT NOT NULL DEFAULT 0.0
);

CREATE UNIQUE INDEX IF NOT EXISTS user_name_index ON users (username);

CREATE TABLE IF NOT EXISTS exchange_rate_history (
    date TEXT PRIMARY KEY CHECK(DATE(STRFTIME("%s", date), "unixepoch") == date),
    timestamp TEXT GENERATED ALWAYS AS (STRFTIME("%s", date)) VIRTUAL,
    value FLOAT
);

CREATE INDEX IF NOT EXISTS exchange_rate_history_date_index ON exchange_rate_history (date);
