# Terraform Azure (production)

Squelette de l'infrastructure Azure. Il lit le groupe de ressources personnel fourni par l'école et prépare les variables communes (tag `user`, IP privée de l'API).

## Utilisation

```powershell
az login
cp terraform.tfvars.example terraform.tfvars   # puis renseigner les valeurs
terraform init
terraform plan
```

## Contraintes Azure du cours

- Tag `user` obligatoire sur toute ressource.
- La VM qui expose l'API a l'IP privée statique `10.241.<index>.4`.
- Quotas : 2 VM (B2s ou B2ms), 2 disques de 64 Go, 1 IP publique, 1 ACR Basic.
- AKS, Container Instances, Load Balancer autonome et Private Endpoints sont bloqués par politique.

Ne jamais commiter `terraform.tfvars` ni les fichiers d'état.
