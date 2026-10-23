-- migrate:up
-- Création des tables du schéma RAW
-- Appeler /current, /readings, /alerts à des fréquences différentes

CREATE TABLE IF NOT EXISTS raw.api_response (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    endpoint      TEXT        NOT NULL,          -- /api/v1/sites/SITE001/current, /api/v1/readings...
    params        JSONB       NOT NULL DEFAULT '{}',
    http_status   INT         NOT NULL,
    fetched_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload       JSONB,                         -- réponse telle quelle
    processed_at  TIMESTAMPTZ                    -- rempli quand l'ETL a transformé la réponse
);
-- Retrouver rapidement les réponses pas encore transformées
CREATE INDEX IF NOT EXISTS ix_api_response_todo
    ON raw.api_response (fetched_at) WHERE processed_at IS NULL;
-- migrate:down