CREATE TABLE IF NOT EXISTS users (
    uuid TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    wallet_usd FLOAT NOT NULL DEFAULT 0.0,
    wallet_btc FLOAT NOT NULL DEFAULT 0.0
);

CREATE UNIQUE INDEX IF NOT EXISTS user_uuid_index ON users (uuid);

CREATE TABLE IF NOT EXISTS revoked_tokens (
    token TEXT PRIMARY KEY,
    expiry TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS token_index ON revoked_tokens (token);

CREATE TABLE IF NOT EXISTS exchange_rate_history (
    date TIMESTAMP WITH TIME ZONE PRIMARY KEY CHECK (date::date = date),
    timestamp FLOAT GENERATED ALWAYS AS (EXTRACT(EPOCH FROM date AT TIME ZONE 'UTC')) STORED,
    value FLOAT
);

CREATE INDEX IF NOT EXISTS exchange_rate_history_date_index ON exchange_rate_history (date);

DROP TYPE IF EXISTS transaction_type;
CREATE TYPE transaction_type AS ENUM ('deposit', 'withdraw', 'buy', 'sell');

CREATE TABLE IF NOT EXISTS transaction_history (
    uuid TEXT PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    user_uuid TEXT NOT NULL REFERENCES users (uuid),
    type transaction_type NOT NULL,
    amount FLOAT NOT NULL,
    total_after_transaction FLOAT NOT NULL
);
