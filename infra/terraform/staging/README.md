# Terraform staging (VM de l'école)

Périmètre prévu : lancer les `docker-compose` des modules sur la VM Proxmox du groupe (staging), et rien d'autre.

- La VM existe déjà : Terraform ne la crée pas.
- Les compose restent la source de vérité des conteneurs : Terraform les déclenche (`git pull` puis `docker compose up -d`), il ne décrit pas les conteneurs.
- La VM n'est joignable que depuis le réseau de l'école : un `apply` part d'un poste de ce réseau, et la CI exigerait un runner auto-hébergé.

À trancher avec l'équipe avant d'écrire du code :
- Terraform apporte-t-il quelque chose par rapport à un simple déploiement SSH en CI ?
- Point d'entrée commun des compose (par exemple un `docker-compose.yml` racine avec `include:`).
- Clé SSH dédiée à Terraform (jamais de mot de passe dans le code).
