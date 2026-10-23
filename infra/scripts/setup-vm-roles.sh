#!/usr/bin/env bash
# Crée les groupes, les comptes de service et les droits des rôles de la VM de staging (issue #39).
# À lancer en root, autant de fois que nécessaire : le script ne fait que combler ce qui manque.
#
# Les personnes de chaque rôle se donnent par variables (noms de comptes Linux déjà créés, séparés
# par des espaces). Aucun nom n'est écrit dans le dépôt.
#   DEVOPS_USERS="..." MLFLOW_USERS="..." MONITORING_USERS="..." infra/scripts/setup-vm-roles.sh
#
# Le script prépare les comptes, les dossiers et les droits ; il n'installe ni MLflow, ni Prometheus,
# ni Grafana.
set -euo pipefail

MLFLOW_DIR="${MLFLOW_DIR:-/srv/mlflow}"
MONITORING_DIR="${MONITORING_DIR:-/srv/monitoring}"

[ "$(id -u)" -eq 0 ] || { echo "À lancer en root" >&2; exit 1; }

if ! command -v visudo >/dev/null; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq sudo
fi

ensure_group() {
  getent group "$1" >/dev/null || groupadd --system "$1"
}

# Compte de service : sans mot de passe, sans shell, propriétaire du dossier de son rôle.
ensure_service_user() {
  local name="$1" dir="$2" mode="$3"
  ensure_group "$name"
  id "$name" >/dev/null 2>&1 \
    || useradd --system --gid "$name" --home-dir "$dir" --no-create-home --shell /usr/sbin/nologin "$name"
  install -d -o "$name" -g "$name" -m "$mode" "$dir"
}

add_members() {
  local group="$1"; shift
  local user extra
  for user in "$@"; do
    id "$user" >/dev/null 2>&1 || { echo "Compte $user introuvable : le créer d'abord (adduser)." >&2; exit 1; }
    usermod -aG "$group" "$user"
    # groupes système éventuels, ajoutés seulement s'ils existent
    for extra in ${EXTRA_GROUPS:-}; do
      getent group "$extra" >/dev/null && usermod -aG "$extra" "$user"
    done
  done
}

# Groupes des personnes.
for group in devops mlflow monitoring; do
  ensure_group "$group"
done

# mlflow : le dossier est écrit par le compte de service ; le groupe peut lire et écrire.
ensure_service_user mlflow "$MLFLOW_DIR" 2770
# monitoring : le groupe peut lire les données et les journaux, sans écrire.
ensure_service_user monitoring "$MONITORING_DIR" 2750

# devops : déclencher et suivre le déploiement. Le groupe docker donne les droits de root sur la
# machine : il est réservé aux personnes de confiance de ce rôle.
sudoers="$(mktemp)"
cat >"$sudoers" <<'EOF'
# Géré par infra/scripts/setup-vm-roles.sh
%devops ALL=(root) NOPASSWD: /usr/bin/systemctl start update-staging.service, \
  /usr/bin/systemctl status update-staging.service, \
  /usr/bin/systemctl status update-staging.timer, \
  /usr/bin/journalctl -u update-staging.service *
EOF
visudo -cf "$sudoers" >/dev/null
install -m 440 -o root -g root "$sudoers" /etc/sudoers.d/devops
rm -f "$sudoers"

# shellcheck disable=SC2086  # les listes de noms sont volontairement découpées sur les espaces
EXTRA_GROUPS="docker" add_members devops ${DEVOPS_USERS:-}
# shellcheck disable=SC2086
EXTRA_GROUPS="" add_members mlflow ${MLFLOW_USERS:-}
# shellcheck disable=SC2086
EXTRA_GROUPS="systemd-journal adm" add_members monitoring ${MONITORING_USERS:-}

echo "Rôles prêts :"
for group in devops mlflow monitoring; do
  echo "  $group : $(getent group "$group" | cut -d: -f4)"
done
echo "Comptes de service (pour 'user:' dans le compose) :"
echo "  mlflow     $(id -u mlflow):$(id -g mlflow)  $MLFLOW_DIR"
echo "  monitoring $(id -u monitoring):$(id -g monitoring)  $MONITORING_DIR"
