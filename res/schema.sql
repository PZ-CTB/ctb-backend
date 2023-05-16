CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

DO $$ BEGIN
    CREATE TYPE transaction_type AS ENUM ('deposit', 'withdraw', 'buy', 'sell');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS transaction_history (
    uuid TEXT PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    user_uuid TEXT NOT NULL REFERENCES users (uuid),
    type transaction_type NOT NULL,
    amount FLOAT NOT NULL,
    total_after_transaction FLOAT NOT NULL
);

CREATE OR REPLACE FUNCTION update_transaction_history()
    RETURNS TRIGGER AS
$$
BEGIN
    IF NEW.wallet_btc <> OLD.wallet_btc THEN
        IF NEW.wallet_btc > OLD.wallet_btc THEN
            INSERT INTO transaction_history (uuid, timestamp, user_uuid, type, amount, total_after_transaction)
            VALUES (uuid_generate_v4(), current_timestamp, NEW.uuid, 'buy', NEW.wallet_btc - OLD.wallet_btc,
                    NEW.wallet_btc);
        ELSE
            INSERT INTO transaction_history (uuid, timestamp, user_uuid, type, amount, total_after_transaction)
            VALUES (uuid_generate_v4(), current_timestamp, NEW.uuid, 'sell', OLD.wallet_btc - NEW.wallet_btc,
                    NEW.wallet_btc);
        END IF;
    ELSIF NEW.wallet_usd <> OLD.wallet_usd THEN
        IF NEW.wallet_usd > OLD.wallet_usd THEN
            INSERT INTO transaction_history (uuid, timestamp, user_uuid, type, amount, total_after_transaction)
            VALUES (uuid_generate_v4(), current_timestamp, NEW.uuid, 'deposit', NEW.wallet_usd - OLD.wallet_usd,
                    NEW.wallet_usd);
        ELSE
            INSERT INTO transaction_history (uuid, timestamp, user_uuid, type, amount, total_after_transaction)
            VALUES (uuid_generate_v4(), current_timestamp, NEW.uuid, 'withdraw', OLD.wallet_usd - NEW.wallet_usd,
                    NEW.wallet_usd);
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_transaction_history_trigger ON users;
CREATE TRIGGER update_transaction_history_trigger
    AFTER UPDATE OF wallet_btc, wallet_usd
    ON users
    FOR EACH ROW
EXECUTE FUNCTION update_transaction_history();
