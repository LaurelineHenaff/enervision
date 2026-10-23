-- migrate:up
CREATE TABLE IF NOT EXISTS ml.prediction (
    target_time    TIMESTAMPTZ NOT NULL,         -- heure prédite
    site_id        TEXT NOT NULL REFERENCES ref.site (site_id),
    model_version  TEXT NOT NULL,                -- version MLflow
    predicted_kw   NUMERIC NOT NULL,
    is_peak        BOOLEAN NOT NULL,
    predicted_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (target_time, site_id, model_version)
);
SELECT create_hypertable('ml.prediction',
                         by_range('target_time', INTERVAL '1 month'),
                         if_not_exists => TRUE);
-- migrate:down