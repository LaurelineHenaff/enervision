# Terraform AWS (production)

Squelette de l'infrastructure de production sur AWS. Il n'a pas encore été appliqué : les informations sur l'accès AWS (compte, région, réseau, droits IAM) ne sont pas toutes connues, et plusieurs valeurs sont des hypothèses à confirmer.

## Ce que le squelette décrit

- Une instance EC2 Debian 13 (même système que la VM du staging) qui fait tourner le `docker-compose.staging.yml` : base, API, ETL et frontend, avec les mêmes images que le staging, promues par le tag de version.
- Un rôle IAM pour l'instance, avec Systems Manager (SSM) : l'administration et le déploiement se font sans SSH ni IP publique.
- Un groupe de sécurité sans aucune entrée par défaut. Le port 8000 de l'API s'ouvre en renseignant `api_ingress_cidrs`.
- Un rôle IAM de déploiement pour GitHub Actions, assumé par OIDC (aucun secret AWS dans GitHub). Il n'est utilisable que par les jobs de l'environnement GitHub `production`, et ne peut que lancer des commandes shell SSM sur cette instance.
- Le script `user_data.sh` installe Docker, l'agent SSM et clone le dépôt dans `/opt/enervision`. Il n'a pas encore tourné sur une vraie instance.

## Utilisation

```powershell
cp terraform.tfvars.example terraform.tfvars   # puis renseigner les valeurs
terraform init
terraform plan
```

Il faut des identifiants AWS dans l'environnement (profil `aws configure`, SSO ou variables `AWS_*`). Le fichier `.terraform.lock.hcl`, créé par `terraform init`, doit être commité.

## Déploiement : `deploy-production.yml`

Le workflow `.github/workflows/deploy-production.yml` se déclenche sur un tag `vX.Y.Z`, posé à la main par le workflow `Release` après la recette du staging. Un premier job écrit un résumé de la version (tag, commit, lien vers les notes) pour l'approbateur ; le job de déploiement attend ensuite l'approbation de l'environnement GitHub `production`, vérifie que les images du tag sont publiées sur GHCR, assume le rôle de déploiement par OIDC, puis lance sur l'instance (SSM Run Command) : `git checkout` du tag, `docker compose pull` et `up -d` avec `IMAGE_TAG=<tag>`, puis attente de `/health`. Il contrôle enfin que l'API annonce `production` et le commit du tag.

Mise en route, dans l'ordre :

1. `terraform apply`, puis relever les sorties `instance_id` et `deploy_role_arn`.
2. Sur l'instance (par SSM Session Manager) : créer `/etc/enervision/production.env` (droits 600) avec `POSTGRES_PASSWORD`, `MOCK_API_URL`, `MOCK_API_USERNAME`, `MOCK_API_PASSWORD`, `APP_ENV=production` (et `COMPOSE_PROFILES=apps` quand `etl` et `frontend` sont prêts), puis faire `docker login ghcr.io` (même jeton `read:packages` que le staging).
3. Dans GitHub, environnement `production` > *Environment variables* : `AWS_REGION`, `AWS_DEPLOY_ROLE_ARN` (sortie `deploy_role_arn`) et `AWS_INSTANCE_ID` (sortie `instance_id`).
4. Dans GitHub, *Settings > Secrets and variables > Actions > Variables* (variable de dépôt) : `PRODUCTION_ENABLED` à `true`. Tant qu'elle est absente, le workflow ne fait rien.

Retour arrière : lancer à la main le workflow « Déploiement en production » (*Run workflow*) en indiquant le tag à restaurer ; l'approbation de l'environnement est la même, et la base est sauvegardée avant le redéploiement (`/var/backups/enervision` sur l'instance, cinq dernières copies). Un lancement manuel s'exécute depuis `main` : l'environnement `production` doit autoriser la branche `main` en plus des tags `v*`. Un tag antérieur à l'ajout du sha dans `/health` échouerait au contrôle final de la version.

## À confirmer ou à décider

- Région, compte AWS, VPC et sous-réseau fournis (variables `region`, `vpc_id`, `subnet_id`).
- Type d'instance (`t3.large` est une hypothèse) et taille du disque, d'après le dimensionnement.
- Exposition de l'API : HTTPS, répartiteur de charge, nom de domaine, IP publique. Rien n'est ouvert pour l'instant.
- État Terraform partagé : bucket S3 (bloc `backend` commenté dans `versions.tf`).
- Secrets de la production (`/etc/enervision/production.env`, jeton GHCR) : à créer sur l'instance par SSM, ou via AWS Secrets Manager. Jamais dans le code.
- Fournisseur OIDC de GitHub : un seul est possible par compte, à désactiver (`create_github_oidc_provider = false`) s'il existe déjà.

Ne jamais commiter `terraform.tfvars` ni les fichiers d'état.
