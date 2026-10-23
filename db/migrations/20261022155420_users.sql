-- migrate:up
-- Table des comptes de l'API (modèle api/app/models/user.py). Jusqu'ici l'API la créait elle-même
-- au démarrage (create_all) : elle existe donc déjà sur les bases de développement et de staging.
-- La migration est écrite pour se rejouer sans erreur sur ces bases comme sur une base vide.
-- En cas de changement du modèle, écrire une nouvelle migration : le schéma ne vient que d'ici.
do $$
begin
    create type public.user_role as enum ('user', 'admin');
exception
    when duplicate_object then null;
end
$$;

create table if not exists public.users (
    id serial primary key,
    email varchar(255) not null,
    hashed_password varchar(255) not null,
    is_active boolean not null,
    role public.user_role not null default 'user',
    created_at timestamptz not null default now()
);

create unique index if not exists ix_users_email on public.users (email);

-- migrate:down
