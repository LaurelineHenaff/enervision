# Déploiement du staging

Le staging tourne sur la VM Proxmox du groupe. La VM n'est pas joignable depuis Internet : elle **tire** les mises à jour, rien n'est poussé vers elle et aucun code externe ne s'y exécute.

## Principe

1. Un merge sur `main` dont la CI est verte lance `publish-images.yml`, qui construit une image par module (dossier avec un `Dockerfile`) et la publie sur GHCR : `ghcr.io/projet-piscine-eadl-enervision/enervision/<module>`, avec les tags `main` et `sha-<commit>`.
2. Toutes les 2 minutes, `update-staging.timer` lance `infra/scripts/update-staging.sh` sur la VM : il aligne le dépôt sur `origin/main`, tire les images puis relance les conteneurs modifiés.
3. Un tag `vX.Y.Z` (créé par le workflow de release) ajoute ce tag à l'image du commit déjà validé, sans reconstruction. La production déploiera cette image.

## Contrat pour les compose

Les services du `docker-compose.staging.yml` racine (le `docker-compose.yml` est le compose de développement : base seule, mot de passe par défaut) référencent les images publiées, par exemple `image: ghcr.io/projet-piscine-eadl-enervision/enervision/etl:${IMAGE_TAG:-main}`. Un `build:` seul ne serait pas mis à jour par ce mécanisme.

## Mise en place sur la VM (une seule fois)

```bash
git clone https://github.com/projet-piscine-eadl-enervision/enervision /opt/enervision
install -d -m 700 /etc/enervision
# créer /etc/enervision/staging.env (droits 600), voir ci-dessous
cp /opt/enervision/infra/scripts/update-staging.{service,timer} /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now update-staging.timer
```

Ce clone est réservé au déploiement : le script le réinitialise sur `origin/main`, il ne faut pas y travailler.

Les images GHCR d'un dépôt public sont privées par défaut : soit les passer en public (*Packages > Package settings > Change visibility*), soit lancer `docker login ghcr.io` sur la VM avec un jeton `read:packages`.

Suivi : `systemctl list-timers update-staging.timer` et `journalctl -u update-staging.service -n 50`.

## Production

Déclenchée par un tag vers Azure, après validation du staging. Pas encore en place : la VM Azure n'existe pas et n'a pas d'IP publique (voir `infra/terraform/azure`).

## Contenu de `/etc/enervision/staging.env`

```
POSTGRES_PASSWORD=...
MOCK_API_URL=...
MOCK_API_USERNAME=...
MOCK_API_PASSWORD=...
# À ajouter quand les images etl et frontend sont publiées sur GHCR :
# COMPOSE_PROFILES=apps
```

Au départ, seule la base TimescaleDB démarre. Les services `etl` et `frontend` sont dans le profil `apps`.
