-- migrate:up
-- Droits : rôles de groupe (sans connexion) et privilèges par module.
-- Les comptes de connexion se créent hors dépôt et héritent de ces rôles.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'enervision_etl') THEN
        CREATE ROLE enervision_etl NOLOGIN; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'enervision_ml') THEN
        CREATE ROLE enervision_ml NOLOGIN; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'enervision_api') THEN
        CREATE ROLE enervision_api NOLOGIN; END IF;
END $$;

-- ETL : lit et écrit raw, ref, core, etl; lit analytics
GRANT USAGE ON SCHEMA raw, ref, core, etl, analytics TO enervision_etl;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA raw, ref, core, etl TO enervision_etl;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA raw, ref, etl TO enervision_etl;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO enervision_etl;

-- ML : lit analytics et ref, écrit ml
GRANT USAGE ON SCHEMA analytics, ref, ml TO enervision_ml;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics, ref TO enervision_ml;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA ml TO enervision_ml;

-- API : lit analytics, ml, ref, core ; écrit app ; gère les comptes (public.users)
GRANT USAGE ON SCHEMA analytics, ml, ref, core, app TO enervision_api;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics, ml, ref, core TO enervision_api;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA app TO enervision_api;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA app TO enervision_api;
GRANT SELECT, INSERT, UPDATE ON public.users TO enervision_api;
GRANT USAGE ON SEQUENCE public.users_id_seq TO enervision_api;

-- Tables créées par les prochaines migrations : mêmes droits automatiquement
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT, INSERT, UPDATE ON TABLES TO enervision_etl;
ALTER DEFAULT PRIVILEGES IN SCHEMA ref, core, etl GRANT SELECT, INSERT, UPDATE ON TABLES TO enervision_etl;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO enervision_etl, enervision_ml, enervision_api;
ALTER DEFAULT PRIVILEGES IN SCHEMA ref GRANT SELECT ON TABLES TO enervision_ml, enervision_api;
ALTER DEFAULT PRIVILEGES IN SCHEMA ml GRANT SELECT, INSERT, UPDATE ON TABLES TO enervision_ml;
ALTER DEFAULT PRIVILEGES IN SCHEMA ml, core GRANT SELECT ON TABLES TO enervision_api;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT, INSERT, UPDATE ON TABLES TO enervision_api;

-- Recalcul de site_baseline par l'ETL.
-- Seul le propriétaire de la vue (le compte des migrations) peut la recalculer.
-- Cette fonction s'exécute avec les droits de son créateur : l'ETL l'appelle sans être propriétaire.
CREATE OR REPLACE FUNCTION analytics.refresh_site_baseline()
RETURNS void
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
    REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.site_baseline;
$$;

REVOKE ALL ON FUNCTION analytics.refresh_site_baseline() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION analytics.refresh_site_baseline() TO enervision_etl;
-- migrate:down