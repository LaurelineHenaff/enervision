#!/usr/bin/env bash
# Génère les requirements.txt figés de chaque module Python à partir de son requirements.in.
# La résolution se fait dans l'image Python des conteneurs, pour que les versions correspondent à l'exécution.
#
# Usage, depuis n'importe quel dossier du projet :
#   ./infra/scripts/compile-requirements.sh                    # tous les modules
#   ./infra/scripts/compile-requirements.sh --upgrade          # met à jour toutes les dépendances
#   ./infra/scripts/compile-requirements.sh --upgrade-package fastapi

set -euo pipefail

PYTHON_IMAGE="python:3.13-slim"
MODULES="api etl ml"

root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

docker run --rm -v "$root:/repo" -w /repo "$PYTHON_IMAGE" sh -c "
  set -e
  pip install -q --root-user-action=ignore pip-tools
  for m in $MODULES; do
    for f in requirements requirements-dev; do
      if [ -f \$m/\$f.in ]; then
        echo \"-> \$m/\$f.txt\"
        pip-compile -q --strip-extras $* \$m/\$f.in -o \$m/\$f.txt
        chown $(id -u):$(id -g) \$m/\$f.txt
      fi
    done
  done
"
