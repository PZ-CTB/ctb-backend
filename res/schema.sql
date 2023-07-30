-- Setup

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users

CREATE TABLE IF NOT EXISTS users
(
    uuid          TEXT PRIMARY KEY,
    email         TEXT  NOT NULL UNIQUE,
    password_hash TEXT,
    wallet_usd    FLOAT NOT NULL DEFAULT 0.0 CHECK (wallet_usd >= 0.0 AND wallet_usd <= 1.0e+12),
    wallet_btc    FLOAT NOT NULL DEFAULT 0.0 CHECK (wallet_btc >= 0.0 AND wallet_btc <= 1.0e+12),
);

CREATE UNIQUE INDEX IF NOT EXISTS user_uuid_index ON users (uuid);

-- Revoked tokens

CREATE TABLE IF NOT EXISTS revoked_tokens
(
    token  TEXT PRIMARY KEY,
    expiry TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS token_index ON revoked_tokens (token);

-- Exchange rate history

CREATE TABLE IF NOT EXISTS exchange_rate_history
(
    date      TIMESTAMP WITH TIME ZONE PRIMARY KEY CHECK (date::date = date),
    timestamp FLOAT GENERATED ALWAYS AS (EXTRACT(EPOCH FROM date AT TIME ZONE 'UTC')) STORED,
    value     FLOAT
);

CREATE INDEX IF NOT EXISTS exchange_rate_history_date_index ON exchange_rate_history (date);

-- Future value

CREATE TABLE IF NOT EXISTS future_value
(
    date      TIMESTAMP WITH TIME ZONE PRIMARY KEY CHECK (date::date = date),
    timestamp FLOAT GENERATED ALWAYS AS (EXTRACT(EPOCH FROM date AT TIME ZONE 'UTC')) STORED,
    value     FLOAT
);

CREATE INDEX IF NOT EXISTS future_value_index ON future_value (date);

-- Transaction history

DO
$$
    BEGIN
        CREATE TYPE transaction_type AS ENUM ('deposit', 'withdraw', 'buy', 'sell');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END
$$;

CREATE TABLE IF NOT EXISTS transaction_history
(
    uuid                        TEXT PRIMARY KEY,
    timestamp                   TIMESTAMP WITH TIME ZONE NOT NULL,
    user_uuid                   TEXT                     NOT NULL REFERENCES users (uuid),
    type                        transaction_type         NOT NULL,
    amount_usd                  FLOAT                    NOT NULL,
    amount_btc                  FLOAT                    NOT NULL,
    total_usd_after_transaction FLOAT                    NOT NULL,
    total_btc_after_transaction FLOAT                    NOT NULL
);

CREATE OR REPLACE FUNCTION update_transaction_history()
    RETURNS TRIGGER AS
$$
BEGIN
    IF NEW.wallet_btc <> OLD.wallet_btc THEN
        IF NEW.wallet_btc > OLD.wallet_btc THEN
            INSERT INTO transaction_history (uuid, timestamp, user_uuid, type, amount_usd, amount_btc,
                                             total_usd_after_transaction, total_btc_after_transaction)
            VALUES (uuid_generate_v4(), current_timestamp, NEW.uuid, 'buy', NEW.wallet_usd - OLD.wallet_usd,
                    NEW.wallet_btc - OLD.wallet_btc, NEW.wallet_usd, NEW.wallet_btc);
        ELSE
            INSERT INTO transaction_history (uuid, timestamp, user_uuid, type, amount_usd, amount_btc,
                                             total_usd_after_transaction, total_btc_after_transaction)
            VALUES (uuid_generate_v4(), current_timestamp, NEW.uuid, 'sell', NEW.wallet_usd - OLD.wallet_usd,
                    NEW.wallet_btc - OLD.wallet_btc, NEW.wallet_usd, NEW.wallet_btc);
        END IF;
    ELSIF NEW.wallet_usd <> OLD.wallet_usd THEN
        IF NEW.wallet_usd > OLD.wallet_usd THEN
            INSERT INTO transaction_history (uuid, timestamp, user_uuid, type, amount_usd, amount_btc,
                                             total_usd_after_transaction, total_btc_after_transaction)
            VALUES (uuid_generate_v4(), current_timestamp, NEW.uuid, 'deposit', NEW.wallet_usd - OLD.wallet_usd,
                    NEW.wallet_btc - OLD.wallet_btc, NEW.wallet_usd, NEW.wallet_btc);
        ELSE
            INSERT INTO transaction_history (uuid, timestamp, user_uuid, type, amount_usd, amount_btc,
                                             total_usd_after_transaction, total_btc_after_transaction)
            VALUES (uuid_generate_v4(), current_timestamp, NEW.uuid, 'withdraw', NEW.wallet_usd - OLD.wallet_usd,
                    NEW.wallet_btc - OLD.wallet_btc, NEW.wallet_usd, NEW.wallet_btc);
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

-- Prevent invalid wallet_usd

CREATE OR REPLACE FUNCTION prevent_invalid_wallet_usd()
    RETURNS TRIGGER AS
$$
BEGIN
    IF NEW.wallet_usd < 0 THEN
        RAISE EXCEPTION 'Cannot perform transaction leading to negative USD balance.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS prevent_invalid_wallet_usd_trigger ON users;
CREATE TRIGGER prevent_invalid_wallet_usd_trigger
    BEFORE UPDATE OF wallet_usd
    ON users
    FOR EACH ROW
EXECUTE FUNCTION prevent_invalid_wallet_usd();

-- Prevent invalid wallet_btc

CREATE OR REPLACE FUNCTION prevent_invalid_wallet_btc()
    RETURNS TRIGGER AS
$$
BEGIN
    IF NEW.wallet_btc < 0 THEN
        RAISE EXCEPTION 'Cannot perform transaction leading to negative BTC balance.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS prevent_invalid_wallet_btc_trigger ON users;
CREATE TRIGGER prevent_invalid_wallet_btc_trigger
    BEFORE UPDATE OF wallet_btc
    ON users
    FOR EACH ROW
EXECUTE FUNCTION prevent_invalid_wallet_btc();
