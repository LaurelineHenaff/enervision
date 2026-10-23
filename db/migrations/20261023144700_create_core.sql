-- migrate:up
-- Création tables du schéma CORE

CREATE TABLE IF NOT EXISTS core.energy_reading (
    time               TIMESTAMPTZ NOT NULL DEFAULT now(),  -- heure de réception (UTC), relevée par notre code
	mock_time          TIMESTAMPTZ NOT NULL,  -- heure donnée par l'api mock important de mettre les deux horaires qui peuvent différer
    site_id              TEXT NOT NULL REFERENCES ref.site (site_id),
    consumption_kw       NUMERIC,
    voltage_v            NUMERIC,
    current_a            NUMERIC,
    power_factor         NUMERIC,
    temperature_celsius  NUMERIC,
    humidity_percent     NUMERIC,
    null_reasons         TEXT[] NOT NULL DEFAULT '{}',
    data_quality         TEXT NOT NULL
                           CHECK (data_quality IN ('good', 'partial', 'degraded', 'critical')),
    source               TEXT NOT NULL CHECK (source IN ('current', 'readings')),
    raw_id               BIGINT REFERENCES raw.api_response (id),
    PRIMARY KEY (site_id, time)
);

-- Hypertable découpée par mois
SELECT create_hypertable('core.energy_reading',
                         by_range('time', INTERVAL '1 month'),
                         if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS core.alert (
    alert_id    TEXT PRIMARY KEY,
    time        TIMESTAMPTZ NOT NULL,
    site_id     TEXT NOT NULL REFERENCES ref.site (site_id),
    severity    TEXT NOT NULL REFERENCES ref.severity (severity),
    alert_type  TEXT NOT NULL REFERENCES ref.alert_type (alert_type),
    message     TEXT,
    value       NUMERIC,
    threshold   NUMERIC,
    origin      TEXT NOT NULL CHECK (origin IN ('api', 'rule'))
);
CREATE INDEX IF NOT EXISTS ix_alert_site_time ON core.alert (site_id, time DESC);

CREATE TABLE IF NOT EXISTS core.sensor_status (
    site_id        TEXT NOT NULL REFERENCES ref.site (site_id),
    sensor         TEXT NOT NULL
                     CHECK (sensor IN ('consumption', 'electrical', 'temperature', 'humidity', 'network')),
    started_at     TIMESTAMPTZ NOT NULL,     -- premier relevé où le capteur est en panne
    failing_until  TIMESTAMPTZ,              -- fin annoncée par /sensors/status
    PRIMARY KEY (site_id, sensor, started_at)
);
CREATE INDEX IF NOT EXISTS ix_sensor_status_site_time ON core.sensor_status (site_id, started_at DESC);
-- migrate:down