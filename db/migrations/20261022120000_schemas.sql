-- migrate:up
create extension if not exists timescaledb;

create schema if not exists raw;        -- réponses brutes de l'API Mock
create schema if not exists ref;        -- référentiels (sites, types, sévérités...)
create schema if not exists core;       -- mesures et alertes transformées
create schema if not exists analytics;  -- agrégats continus
create schema if not exists ml;         -- prédictions
create schema if not exists app;        -- recommandations
create schema if not exists etl;        -- journal des exécutions

-- migrate:down
-- Correction en avant : on n'écrit pas de retour arrière (voir docs/migrations-base-de-donnees.md).
-- dbmate exige tout de même ce bloc, qui reste vide.
