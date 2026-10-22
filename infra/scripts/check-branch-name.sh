#!/usr/bin/env bash
# Vérifie le nom d'une branche. Même règle pour la CI (job branch-name) et pour le hook local pre-commit.
#
# Usage : check-branch-name.sh [branche]   (branche courante par défaut)
set -euo pipefail

branch="${1:-$(git symbolic-ref --short -q HEAD || true)}"

# HEAD détaché (rebase en cours, checkout d'un tag) : pas de nom à vérifier.
[ -n "$branch" ] || exit 0

# dependabot crée ses propres branches.
[[ "$branch" == dependabot/* ]] && exit 0

if [[ ! "$branch" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ || ${#branch} -gt 50 ]]; then
  message="Nom de branche invalide : '$branch'. Attendu : minuscules et tirets, sans préfixe ni slash, 50 caractères maximum (ex. endpoint-readings)."
  if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
    echo "::error::$message"
  else
    echo "$message" >&2
  fi
  exit 1
fi
