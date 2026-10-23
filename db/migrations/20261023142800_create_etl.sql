-- migrate:up
-- Création des tables du schéma ETL
CREATE TABLE IF NOT EXISTS etl.run (
    run_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_type       TEXT NOT NULL,
    started_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at    TIMESTAMPTZ,
    status         TEXT NOT NULL DEFAULT 'running'
                     CHECK (status IN ('running', 'success', 'failed')),
    period_start   TIMESTAMPTZ,                  -- période de mesure traitée
    period_end     TIMESTAMPTZ,
    rows_loaded    INT NOT NULL DEFAULT 0,
    rows_rejected  INT NOT NULL DEFAULT 0,
    error_message  TEXT
);
CREATE INDEX IF NOT EXISTS ix_run_type_started ON etl.run (run_type, started_at DESC);
-- migrate:down