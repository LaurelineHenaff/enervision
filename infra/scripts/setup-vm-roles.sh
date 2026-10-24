#!/usr/bin/env bash
# Crée les comptes de service de la VM de staging (issue #39) : mlflow et monitoring, sans mot de
# passe ni shell, propriétaires de leur dossier. À lancer en root, autant de fois que nécessaire :
# le script ne fait que combler ce qui manque.
#
# Il ne touche à aucun compte de personne (droits, groupes, sudo) : l'administration reste faite
# en root. Il n'installe ni MLflow, ni Prometheus, ni Grafana.
set -euo pipefail

MLFLOW_DIR="${MLFLOW_DIR:-/srv/mlflow}"
MONITORING_DIR="${MONITORING_DIR:-/srv/monitoring}"

[ "$(id -u)" -eq 0 ] || { echo "À lancer en root" >&2; exit 1; }

ensure_service_user() {
  local name="$1" dir="$2" mode="$3"
  getent group "$name" >/dev/null || groupadd --system "$name"
  id "$name" >/dev/null 2>&1 \
    || useradd --system --gid "$name" --home-dir "$dir" --no-create-home --shell /usr/sbin/nologin "$name"
  install -d -o "$name" -g "$name" -m "$mode" "$dir"
}

# mlflow : le groupe peut lire et écrire. monitoring : le groupe peut lire.
ensure_service_user mlflow "$MLFLOW_DIR" 2770
ensure_service_user monitoring "$MONITORING_DIR" 2750

echo "Comptes de service (pour 'user:' dans le compose) :"
echo "  mlflow     $(id -u mlflow):$(id -g mlflow)  $MLFLOW_DIR"
echo "  monitoring $(id -u monitoring):$(id -g monitoring)  $MONITORING_DIR"
