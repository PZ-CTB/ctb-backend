
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password_hash TEXT
);

CREATE TABLE IF NOT EXISTS exchange_rate_history (
    date TEXT PRIMARY KEY CHECK(DATE(STRFTIME("%s", date), "unixepoch") == date),
    timestamp TEXT GENERATED ALWAYS AS (STRFTIME("%s", date)) VIRTUAL,
    value FLOAT
);