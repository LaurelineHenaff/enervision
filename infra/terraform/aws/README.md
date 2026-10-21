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

## À confirmer ou à décider

- Région, compte AWS, VPC et sous-réseau fournis (variables `region`, `vpc_id`, `subnet_id`).
- Type d'instance (`t3.large` est une hypothèse) et taille du disque, d'après le dimensionnement.
- Exposition de l'API : HTTPS, répartiteur de charge, nom de domaine, IP publique. Rien n'est ouvert pour l'instant.
- État Terraform partagé : bucket S3 (bloc `backend` commenté dans `versions.tf`).
- Secrets de la production (`/etc/enervision/staging.env`, jeton GHCR) : à créer sur l'instance par SSM, ou via AWS Secrets Manager. Jamais dans le code.
- Workflow `deploy-production.yml`, déclenché sur tag, avec l'environnement GitHub `production`.
- Fournisseur OIDC de GitHub : un seul est possible par compte, à désactiver (`create_github_oidc_provider = false`) s'il existe déjà.

Ne jamais commiter `terraform.tfvars` ni les fichiers d'état.
