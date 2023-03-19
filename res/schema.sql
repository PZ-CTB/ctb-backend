CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT,
    wallet_usd FLOAT NOT NULL DEFAULT 0.0,
    wallet_btc FLOAT NOT NULL DEFAULT 0.0
);

CREATE UNIQUE INDEX IF NOT EXISTS user_name_index ON users (email);

CREATE TABLE IF NOT EXISTS revoked_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL,
    expiry TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS token_index ON revoked_tokens (token);

CREATE TABLE IF NOT EXISTS exchange_rate_history (
    date TEXT PRIMARY KEY CHECK(DATE(STRFTIME("%s", date), "unixepoch") == date),
    timestamp TEXT GENERATED ALWAYS AS (STRFTIME("%s", date)) VIRTUAL,
    value FLOAT
);

CREATE INDEX IF NOT EXISTS exchange_rate_history_date_index ON exchange_rate_history (date);
