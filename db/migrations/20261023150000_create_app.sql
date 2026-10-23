-- migrate:up
-- Table qui stocke les recommandations donnees par site
CREATE TABLE IF NOT EXISTS app.recommendation (
    recommendation_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recommendation_type_id  INT  NOT NULL REFERENCES ref.recommendation_type (recommendation_type_id),
    site_id                 TEXT NOT NULL REFERENCES ref.site (site_id),
    target_time             TIMESTAMPTZ NOT NULL,   -- heure de l'alerte prévu
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (recommendation_type_id, site_id, target_time)
);
-- migrate:down