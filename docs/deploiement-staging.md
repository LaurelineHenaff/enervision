# Déploiement du staging

Le staging tourne sur la VM Proxmox du groupe. Un push sur `main` dont la CI est verte lance le workflow `deploy-staging.yml`, exécuté par un runner GitHub auto-hébergé installé sur cette VM.

## Mise en place du runner (une seule fois)

1. Dans GitHub : *Settings > Actions > Runners > New self-hosted runner* (Linux x64). Suivre les commandes affichées sur la VM, en ajoutant le label `staging`.
2. Faire tourner le runner avec un utilisateur non root appartenant au groupe `docker`, installé en service (`./svc.sh install`).
3. Créer `/etc/enervision/staging.env` (droits `600`) avec les variables des services, par exemple `MOCK_API_URL`, `MOCK_API_USERNAME` et `MOCK_API_PASSWORD`.
4. Dans GitHub : créer l'environnement `staging`.
5. Dans *Settings > Actions > General*, exiger l'approbation pour les workflows des contributeurs externes.

## Sécurité

Le dépôt est public : un runner auto-hébergé exécute le code qu'on lui envoie. Le workflow n'écoute donc que `workflow_run` sur `main` (jamais `pull_request`), et le runner ne doit servir qu'à ce workflow.

## Production

La production sera déclenchée par un tag, après validation du staging, vers Azure. Elle n'est pas encore en place : la VM Azure n'existe pas et n'a pas d'IP publique (voir `infra/terraform/azure`).
