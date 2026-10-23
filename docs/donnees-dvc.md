# Données volumineuses avec DVC

Les fichiers lourds ne vont pas dans Git. DVC les suit : Git garde un petit fichier pointeur (`.dvc`), les données vivent dans un stockage partagé et dans le cache local `.dvc/cache` (ignoré par Git).

## Stockages

| Nom | Usage | Adresse | État |
|---|---|---|---|
| (cache local) | développement | `.dvc/cache` | rempli par `dvc pull` ou `dvc repro` |
| `preprod` (défaut) | VM de préproduction | `ssh://10.43.43.50/var/lib/enervision/dvc` | vérifié le 23/10/2026 : push puis pull depuis un clone propre |
| `prod` | production | `s3://enervision-production-data-136825753193/dvc` | vérifié le 23/10/2026 : bucket de `infra/terraform/aws/s3.tf` (région `eu-west-3`, préfixe `dvc/`), push puis pull depuis un clone propre |

Aucun chemin ni identifiant personnel n'est versionné. Chacun renseigne les siens dans `.dvc/config.local` (ignoré par Git) :

```bash
pip install "dvc[ssh,s3]"
dvc remote modify --local preprod user <compte>
dvc remote modify --local preprod keyfile ~/.ssh/<clé>      # ou password
dvc remote modify --local prod profile enervision
```

Pour S3, ouvrir d'abord une session : `aws sso login --profile enervision --use-device-code` (la session expire, le `push` échoue ensuite avec une erreur d'identifiants).

## Usage

```bash
dvc pull                    # télécharge depuis le stockage par défaut (preprod)
dvc pull -r prod            # depuis la production
dvc push                    # envoie les nouveaux fichiers
dvc add chemin/fichier      # suit un nouveau fichier, puis git add du .dvc créé
```

## Fichiers suivis

| Fichier | Pointeur | Origine |
|---|---|---|
| `etl/pipeline/provided_files/all_sites_combined.csv` | `.dvc` à côté | fourni par l'école, 122 647 lignes, 7 sites, 2023-2024 |
| `etl/pipeline/provided_files/dataset_metadata.json` | `.dvc` à côté | fourni par l'école |
| `etl/pipeline/edited_files/energy_consumption_cleaned.parquet` | `etl/dvc.yaml`, `etl/dvc.lock` | produit par `dvc repro` |

## À faire

- Donner un accès SSH à l'équipe sur la VM de préproduction (elle n'a qu'un compte root à ce jour : la clé de chaque membre est à ajouter dans `authorized_keys`).
- Les droits d'écriture sous `dvc/` n'ont été testés qu'avec le rôle `AdministratorAccess` : la politique de l'instance EC2 n'y donne que la lecture, la poussée se fait depuis les postes.
- `terraform destroy` vide le bucket (`force_destroy`) : les données de `prod` se repoussent depuis `preprod` ou le poste d'un membre.
