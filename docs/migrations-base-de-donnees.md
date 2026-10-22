# Migrations de la base de données

Ce document décrit comment le schéma de la base (TimescaleDB sur PostgreSQL 16) est versionné et mis à jour, de façon identique sur les postes de développement, le staging et la production. Les règles courtes sont dans le [`CONTRIBUTING.md`](../CONTRIBUTING.md).

Documents liés : [déploiement du staging](deploiement-staging.md) et [mise en production](mise-en-production.md).

## 1. Principe

Le schéma n'est jamais modifié à la main. Chaque changement est un fichier SQL de `db/migrations/`, appliqué automatiquement par [dbmate](https://github.com/amacneil/dbmate) :

```
db/migrations/*.sql -> image db (CI) -> service migrate -> base à jour -> api et etl démarrent
```

- Le module `db/` a un `Dockerfile` : la CI en publie l'image sur GHCR comme celle des autres modules, avec les tags `main`, `sha-<commit>` et `vX.Y.Z`. Les migrations voyagent donc **avec l'image**, et la production reçoit exactement le jeu de migrations recetté au staging.
- Le service `migrate` des compose lance cette image à chaque `up`, une fois la base saine, et s'arrête. `api` et `etl` ne démarrent qu'après sa réussite (`service_completed_successfully`). Si une migration échoue, ils ne démarrent pas et le journal de `migrate` donne l'erreur.
- dbmate note chaque migration appliquée dans la table `schema_migrations` et n'applique que celles qui manquent. Un deuxième lancement ne fait rien : le minuteur du staging, qui relance la pile toutes les 2 minutes, relance donc `migrate` sans effet. Un verrou évite que deux exécutions simultanées se marchent dessus.
- Le service `migrate` n'a pas de politique de redémarrage (`restart: "no"`) : un service ponctuel relancé en boucle fausserait `service_completed_successfully`.

## 2. Écrire une migration

Créer un fichier dont le nom est la date et l'heure de création, suivie du sujet :

```bash
touch db/migrations/$(date +%Y%m%d%H%M%S)_ajout-table-site.sql
```

Le contenu a toujours deux blocs. Le bloc `down` est exigé par dbmate (sans lui, la migration est refusée), mais l'équipe ne s'en sert pas : il reste vide ou ne contient qu'un commentaire.

```sql
-- migrate:up
create table ref.site_type (
    site_type text primary key,
    label     text not null
);

-- migrate:down
```

Chaque migration s'exécute dans une transaction : si une instruction échoue, rien n'est appliqué. Pour une instruction qui ne peut pas tourner dans une transaction, dbmate propose `-- migrate:up transaction:false` (à tester avant usage).

Pour l'appliquer en local, `docker compose up -d` suffit : le dossier `db/migrations` est monté dans le conteneur, sans reconstruire l'image. Pour la relancer seule ou voir l'état :

```bash
docker compose run --rm migrate          # applique ce qui manque
docker compose run --rm migrate status   # liste appliquées et en attente
```

Pour repartir d'une base vide, `docker compose down -v` supprime le volume `pgdata` (et donc toutes les données locales), puis `docker compose up -d` recrée tout depuis les migrations.

## 3. Règles

- **On ne modifie jamais une migration fusionnée.** dbmate ne contrôle pas l'empreinte des fichiers déjà appliqués : un fichier modifié après coup ne serait pas rejoué, et les bases divergeraient en silence. Le job `migrations` de la CI refuse donc toute PR qui modifie, renomme ou supprime un fichier existant. Une erreur se corrige par une nouvelle migration.
- **On corrige en avant.** Il n'y a pas de retour arrière automatique du schéma.
- **Chaque migration reste compatible avec la version précédente du code.** Un retour arrière du staging ou de la production relance l'ancienne image sur la base déjà migrée : les anciens `api` et `etl` doivent encore fonctionner. En pratique : ajouter une colonne nullable plutôt qu'obligatoire, ne pas renommer ni supprimer en une seule étape (ajouter le nouveau, basculer le code, supprimer l'ancien dans une version suivante).
- **Aucun secret.** Pas de mot de passe de rôle dans un fichier de migration : les rôles de connexion se créent hors dépôt, avec les variables d'environnement. Les droits (`grant`) peuvent en revanche être versionnés.
- **Les données de référence** (`ref.*`) sont des migrations, avec `insert ... on conflict do nothing` pour rester rejouables sans erreur.

## 4. Ce que vérifie la CI

Le job `migrations` de `ci.yml`, exigé par `ci-ok` :

1. sur une PR, aucune migration existante n'est modifiée, renommée ni supprimée (`git diff --diff-filter=MDR` contre la branche de base) ;
2. l'image `db` est construite, puis ses migrations sont appliquées sur un TimescaleDB vide, **deux fois** de suite (la seconde ne doit rien changer), puis `status` doit indiquer qu'aucune migration n'est en attente.

Comme `main` exige une branche à jour avant le merge, ce job rejoue l'ensemble des migrations après chaque rebase : deux PR qui touchent le même objet sont détectées avant d'arriver sur `main`.

## 5. Plusieurs PR en parallèle

dbmate applique toutes les migrations manquantes, quelle que soit leur date : une migration plus ancienne fusionnée après une plus récente déjà appliquée sur le staging est appliquée normalement, sans réglage. Le nom horodaté évite les collisions de numéro entre deux PR.

## 6. TimescaleDB

Une hypertable, un agrégat continu (créé avec `WITH NO DATA`) et sa politique de rafraîchissement peuvent être créés dans la même migration transactionnelle, ce qui a été vérifié sur la version utilisée (2.30.2). L'agrégat se remplit ensuite par sa politique : ne pas appeler `refresh_continuous_aggregate()` dans une migration.

## 7. Cas particuliers

- **Modification manuelle de la base.** Rien n'empêche aujourd'hui de modifier la base à la main (`psql`, outil de l'IDE) sur un poste de développement ou sur la VM : toutes les applications se connectent avec le même compte, qui a tous les droits. dbmate ne détecte pas l'écart et la CI ne voit que les fichiers du dépôt. Une base modifiée à la main n'est plus celle que décrivent les migrations, et la migration suivante peut échouer chez toi seulement (objet déjà existant, colonne absente). **Remède sur un poste de développement : `docker compose down -v` puis `docker compose up -d`**, qui recrée la base depuis les migrations (les données locales sont perdues, pas le schéma voulu). Un changement voulu se fait toujours par une migration. Seul un compte d'application sans droit de modifier le schéma l'empêcherait techniquement : ce n'est pas encore en place.

- **Premier déploiement d'une nouvelle image `db`.** Le compose de `main` référence `.../db:main` dès le merge, alors que l'image n'existe qu'une fois la CI et la publication terminées. Tant qu'elle manque, le `pull` du minuteur échoue et le staging ne se met pas à jour : l'erreur disparaît seule au passage suivant, une fois l'image publiée.
- **Retour arrière.** Le staging figé sur un `IMAGE_TAG` ancien relance l'ancienne image `db`, dont les migrations sont déjà appliquées : `migrate` ne fait rien et sort en succès. Une base plus récente que le code ne bloque donc pas le démarrage, d'où la règle de compatibilité du paragraphe 3. Un tag antérieur à l'introduction de `db` n'a ni service `migrate` ni image `db`, et le service disparaît (`--remove-orphans`).
- **Sauvegarde.** La production fait un `pg_dump` avant chaque déploiement (voir [`mise-en-production.md`](mise-en-production.md)) : c'est la seule façon de revenir à un schéma antérieur.
