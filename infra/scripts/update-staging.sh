#!/usr/bin/env bash
# Met à jour le staging : récupère les compose de main, tire les nouvelles images, relance ce qui a changé.
# Lancé toutes les 2 minutes par update-staging.timer. Sans effet si rien n'a changé.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/enervision}"
ENV_FILE="${ENV_FILE:-/etc/enervision/staging.env}"
COMPOSE_FILE_STAGING="docker-compose.staging.yml"
export COMPOSE_PROJECT_NAME=enervision

exec 9>/var/lock/update-staging.lock
flock -n 9 || { echo "Mise à jour déjà en cours"; exit 0; }

cd "$REPO_DIR"
git fetch --quiet origin main
git reset --hard --quiet origin/main

[ -f "$COMPOSE_FILE_STAGING" ] || { echo "$COMPOSE_FILE_STAGING absent à la racine" >&2; exit 1; }
[ -f "$ENV_FILE" ] || { echo "$ENV_FILE absent" >&2; exit 1; }

# Version figée à la main (retour arrière d'urgence) : le staging ne suit plus main tant que la ligne est là.
if grep -Eq '^[[:space:]]*IMAGE_TAG=' "$ENV_FILE"; then
  echo "ATTENTION : IMAGE_TAG est défini dans $ENV_FILE, le staging est figé sur une version et ne suit plus main. Retirer la ligne une fois le correctif fusionné." >&2
fi

docker compose -f "$COMPOSE_FILE_STAGING" --env-file "$ENV_FILE" pull --ignore-buildable --quiet
docker compose -f "$COMPOSE_FILE_STAGING" --env-file "$ENV_FILE" up -d --remove-orphans
