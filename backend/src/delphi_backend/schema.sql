CREATE TABLE IF NOT EXISTS crypto_markets (
    condition_id  text PRIMARY KEY,
    question      text NOT NULL,
    slug          text NOT NULL,
    asset         text NOT NULL,
    target_price  numeric NOT NULL,
    deadline      timestamptz NOT NULL,
    event_type    text NOT NULL,
    direction     text NOT NULL,
    discovered_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS forecasts (
    condition_id               text PRIMARY KEY REFERENCES crypto_markets(condition_id),
    spot_price                 numeric NOT NULL,
    sigma                      numeric NOT NULL,
    model_probability          numeric NOT NULL,
    market_implied_probability numeric,
    edge                       numeric,
    updated_at                 timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS api_health (
    api_name        text PRIMARY KEY,
    status          text NOT NULL,
    latency_ms      numeric,
    last_checked_at timestamptz NOT NULL,
    last_success_at timestamptz,
    last_error      text
);

CREATE TABLE IF NOT EXISTS app_events (
    id      bigserial PRIMARY KEY,
    ts      timestamptz NOT NULL DEFAULT now(),
    level   text NOT NULL,
    api     text,
    step    text NOT NULL,
    message text NOT NULL,
    detail  jsonb
);

CREATE INDEX IF NOT EXISTS app_events_ts_idx ON app_events (ts DESC);
CREATE INDEX IF NOT EXISTS app_events_api_ts_idx ON app_events (api, ts DESC);

ALTER TABLE crypto_markets ADD COLUMN IF NOT EXISTS last_seen_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE crypto_markets ADD COLUMN IF NOT EXISTS delisted_at timestamptz;

CREATE INDEX IF NOT EXISTS crypto_markets_delisted_idx ON crypto_markets (delisted_at);

CREATE TABLE IF NOT EXISTS forecast_history (
    id                         bigserial PRIMARY KEY,
    condition_id               text NOT NULL REFERENCES crypto_markets(condition_id) ON DELETE CASCADE,
    spot_price                 numeric NOT NULL,
    sigma                      numeric NOT NULL,
    model_probability          numeric NOT NULL,
    market_implied_probability numeric,
    edge                       numeric,
    years_to_deadline          numeric NOT NULL,
    recorded_at                timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS forecast_history_market_idx
    ON forecast_history (condition_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS market_resolutions (
    condition_id   text PRIMARY KEY REFERENCES crypto_markets(condition_id) ON DELETE CASCADE,
    outcome        boolean NOT NULL,
    outcome_prices text NOT NULL,
    resolved_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS news_items (
    url          text PRIMARY KEY,
    title        text NOT NULL,
    source       text NOT NULL,
    summary      text,
    published_at timestamptz,
    fetched_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS news_items_published_idx
    ON news_items (published_at DESC NULLS LAST);
