# Données versionnées avec DVC

Les fichiers de données (CSV bruts, métadonnées JSON, parquet silver) ne vont pas dans Git : ils sont trop lourds et changent à chaque nettoyage. [DVC](https://dvc.org/doc) les envoie dans un bucket S3 et ne laisse dans Git qu'un petit fichier `.dvc` par fichier ou dossier, qui contient son empreinte. Un commit Git désigne donc une version précise des données.

## Où sont les données

| Dossier | Contenu |
|---|---|
| `etl/data/raw/` | Fichiers fournis : `SITE00x.csv`, `*_metadata.json`, `all_sites_combined.csv`, `dataset_metadata.json` |
| `etl/data/silver/` | Sortie du nettoyage : `conso_energie_nettoyee.parquet`, chargé en base par `python -m loaders.silver` |

Les dossiers sont sous `etl/` parce que ce dossier est monté dans le conteneur `etl` : le chargement y lit directement `data/silver/...`.

Remote DVC : `s3://enervision-eadl-dvc/store` (région `eu-west-3`), décrit dans `.dvc/config`. Le bucket et le groupe IAM `enervision-dvc` qui y donne accès sont créés par Terraform (`infra/terraform/aws/dvc.tf`).

## Installation (une fois par poste)

```bash
pip install "dvc[s3]==3.67.1"
```

DVC utilise les identifiants AWS du poste, comme Terraform (`aws configure`, SSO ou variables `AWS_*`). Le compte doit faire partie du groupe IAM `enervision-dvc`.

## Récupérer les données

```bash
git pull
dvc pull            # télécharge les fichiers qui correspondent aux .dvc du commit courant
```

## Ajouter ou mettre à jour un fichier

```bash
dvc add etl/data/silver/conso_energie_nettoyee.parquet   # crée ou met à jour le .dvc, et l'ajoute à Git
git commit -m "feat(etl): nouvelle version du silver"
dvc push            # envoie le fichier dans S3
git push
```

Toujours faire `dvc push` avant `git push` : sinon les autres récupèrent un `.dvc` dont le fichier n'est pas dans S3.

Revenir à une version précédente des données : `git checkout <commit> -- etl/data/silver/conso_energie_nettoyee.parquet.dvc`, puis `dvc checkout`.

## Mise en route (une seule fois)

1. `terraform apply` dans `infra/terraform/aws` crée le bucket et le groupe IAM. Si le nom `enervision-eadl-dvc` est déjà pris dans AWS, changer `dvc_bucket_name` et l'URL dans `.dvc/config`.
2. Ajouter chaque membre de l'équipe au groupe IAM `enervision-dvc`.
3. Déplacer les fichiers de données sous `etl/data/`, les retirer de Git (`git rm --cached`), puis `dvc add`, `dvc push` et commit.
