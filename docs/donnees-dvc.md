# Données volumineuses avec DVC

Les fichiers lourds ne vont pas dans Git. DVC les suit : Git garde un petit fichier pointeur (`.dvc`), les données vivent dans un stockage partagé et dans le cache local `.dvc/cache` (ignoré par Git).

## Stockages

| Nom | Usage | Adresse | État |
|---|---|---|---|
| (cache local) | développement | `.dvc/cache` | rempli par `dvc pull` ou `dvc repro` |
| `preprod` (défaut) | VM de préproduction | `ssh://10.43.43.50/var/lib/enervision/dvc` | dossier à créer sur la VM, non vérifié |
| `prod` | production | `s3://enervision-production-data-136825753193` | non vérifié, accès AWS indisponible |

Aucun chemin ni identifiant personnel n'est versionné. Chacun renseigne les siens dans `.dvc/config.local` (ignoré par Git) :

```bash
pip install "dvc[ssh,s3]"
dvc remote modify --local preprod user <compte>
dvc remote modify --local preprod keyfile ~/.ssh/<clé>      # ou password
dvc remote modify --local prod profile <profil-aws>
```

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

- Créer le dossier de stockage sur la VM de préproduction et donner un accès SSH à l'équipe (la VM n'a qu'un compte root à ce jour), puis lancer `dvc push`.
- Tant que personne n'a poussé, les fichiers fournis ne sont disponibles que sur le poste qui les a ajoutés : ils viennent de l'école, qui peut les redonner.
- Créer le bucket de production et ses droits IAM avant de s'en servir.
