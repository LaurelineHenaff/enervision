-- migrate:up
-- Vues du schéma ANALYTICS

-- Par minute
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.energy_minute
WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
SELECT
    time_bucket(INTERVAL '1 minute', time)               AS minute,
    site_id,
    avg(consumption_kw)                                  AS avg_consumption_kw,
    max(consumption_kw)                                  AS max_consumption_kw,
    count(*)                                             AS nb_readings,
    count(*) FILTER (WHERE consumption_kw IS NULL)       AS nb_missing
FROM core.energy_reading
GROUP BY minute, site_id
WITH NO DATA;

-- Par heure
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.energy_hourly
WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
SELECT
    time_bucket(INTERVAL '1 hour', time)                 AS hour,
    site_id,
    avg(consumption_kw)                                  AS avg_consumption_kw,
    max(consumption_kw)                                  AS max_consumption_kw,
    avg(consumption_kw)                                  AS energy_kwh,   -- kW moyen × 1 h
    avg(temperature_celsius)                             AS avg_temperature_celsius,
    count(*)                                             AS nb_readings,
    count(*) FILTER (WHERE consumption_kw IS NULL)       AS nb_missing
FROM core.energy_reading
GROUP BY hour, site_id
WITH NO DATA;

-- Par jour
CREATE OR REPLACE VIEW analytics.energy_daily AS
SELECT
    time_bucket(INTERVAL '1 day', hour, 'Europe/Paris')  AS day,
    site_id,
    sum(energy_kwh)                                      AS energy_kwh,
    max(max_consumption_kw)                              AS max_consumption_kw,
    sum(nb_readings)                                     AS nb_readings,
    sum(nb_missing)                                      AS nb_missing
FROM analytics.energy_hourly
GROUP BY day, site_id;

-- Dernière consommation non nulle par site
CREATE OR REPLACE VIEW analytics.latest_reading AS
SELECT
    s.site_id,
    v.consumption_kw,                        -- dernière consommation non nulle
    now() - v.received_at  AS age,           -- âge de cette valeur
    d.data_quality         AS last_quality   -- qualité du tout dernier relevé
FROM ref.site s
LEFT JOIN LATERAL (
    SELECT consumption_kw, received_at
    FROM core.energy_reading e
    WHERE e.site_id = s.site_id AND e.consumption_kw IS NOT NULL
    ORDER BY e.time DESC
    LIMIT 1
) v ON TRUE
LEFT JOIN LATERAL (
    SELECT data_quality
    FROM core.energy_reading e
    WHERE e.site_id = s.site_id
    ORDER BY e.time DESC
    LIMIT 1
) d ON TRUE;

SELECT add_continuous_aggregate_policy('analytics.energy_minute',
    start_offset => INTERVAL '1 hour', end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('analytics.energy_hourly',
    start_offset => INTERVAL '3 days', end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '15 minutes', if_not_exists => TRUE);
-- migrate:down