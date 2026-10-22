#!/usr/bin/env bash
# Vérifie les messages de tous les commits que la branche ajoute à origin/main, comme le job
# commit-messages de la CI. Lancé par le hook pre-push (voir .pre-commit-config.yaml), donc avec
# commitlint dans le PATH ; rattrape les commits faits sans les hooks de commit.
set -euo pipefail

if ! base=$(git merge-base origin/main HEAD 2>/dev/null); then
  echo "origin/main introuvable en local (git fetch origin) : messages non vérifiés." >&2
  exit 0
fi

commitlint --config .commitlintrc.yml --from "$base" --to "${PRE_COMMIT_TO_REF:-HEAD}"
