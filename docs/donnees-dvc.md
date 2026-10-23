# Données volumineuses avec DVC

Les fichiers lourds ne vont pas dans Git. DVC les suit : Git garde un petit fichier pointeur (`.dvc` ou `dvc.lock`), les données vivent dans un stockage partagé et dans un cache local (`.dvc/cache`, ignoré par Git).

## Où sont les données

| Stockage | Rôle | Adresse |
|---|---|---|
| `preprod` (par défaut) | VM de préproduction | `ssh://10.43.43.50/var/lib/enervision/dvc` |
| `prod` | production | `s3://enervision-production-data-136825753193/dvc` (bucket de `infra/terraform/aws/s3.tf`) |

Les deux ont été vérifiés le 23/10/2026 : envoi, puis récupération depuis un clone propre, avec le même hash pour le CSV.

## Mise en place, une seule fois

**1. Installer DVC.** Il n'est pas dans les `requirements` du projet (il est lourd et ne sert qu'aux données). Une installation à part, sans droits administrateur :

```bash
python3 -m venv ~/.local/share/dvc-venv
~/.local/share/dvc-venv/bin/pip install "dvc[ssh,s3]"
ln -sf ~/.local/share/dvc-venv/bin/dvc ~/.local/bin/dvc
dvc --version
```

Il faut bien `dvc[ssh,s3]` et non `dvc` seul, sinon DVC répond « ssh is supported, but requires 'dvc-ssh' ».

**2. Accès SSH à la VM de préproduction.** Ajouter sa clé sur la VM (le mot de passe root est dans les notes Teams) :

```bash
ssh-keygen -t ed25519            # si vous n'avez pas encore de clé
ssh-copy-id root@10.43.43.50
```

**3. Accès AWS.** Suivre [`aws-poste-developpeur.md`](aws-poste-developpeur.md) pour le profil `enervision`.

**4. Réglages personnels** dans votre clone. Ils vont dans `.dvc/config.local`, qui n'est jamais commité (rien de personnel dans `.dvc/config`) :

```bash
dvc remote modify --local preprod user root
dvc remote modify --local prod profile enervision
```

## Chaque jour

Avant de toucher à `prod` : `aws sso login --profile enervision --use-device-code`. La session SSO expire, et le `push` ou le `pull` échoue alors avec une erreur d'identifiants AWS.

Pour éviter de retaper la passphrase SSH à chaque commande : `eval "$(ssh-agent -s)" && ssh-add`.

```bash
dvc pull                   # récupère les fichiers depuis preprod
dvc pull -r prod           # ou depuis la production
cd etl && dvc repro        # reconstruit le parquet nettoyé si le script ou le CSV a changé
dvc status                 # fichiers modifiés par rapport aux pointeurs
dvc status -c -r prod      # fichiers absents du stockage
```

## Quand les données changent

Les données d'abord, Git ensuite : si le `git push` part avant le `dvc push`, vos collègues récupèrent un pointeur dont les fichiers n'existent nulle part (« missing cache »).

**Nouveau fichier lourd :**

```bash
dvc add chemin/du/fichier           # crée chemin/du/fichier.dvc et l'ajoute au .gitignore
git add chemin/du/fichier.dvc chemin/du/.gitignore
dvc push && dvc push -r prod
git commit -m "feat: suivre <fichier> avec DVC"
```

**Script de nettoyage modifié :**

```bash
cd etl && dvc repro                 # met à jour etl/dvc.lock
dvc push && dvc push -r prod
git add etl/dvc.lock etl/pipeline/clean_history.py
```

Règles : jamais un fichier de données dans Git ; jamais d'identifiant dans `.dvc/config` ; envoyer sur les deux stockages quand un jeu de données change.

## Fichiers suivis

| Fichier | Pointeur | Origine |
|---|---|---|
| `etl/pipeline/provided_files/all_sites_combined.csv` | `.dvc` à côté | fourni par l'école, 122 647 lignes, 7 sites, 2023 à 2024 |
| `etl/pipeline/provided_files/dataset_metadata.json` | `.dvc` à côté | fourni par l'école |
| `etl/pipeline/edited_files/energy_consumption_cleaned.parquet` | `etl/dvc.yaml` et `etl/dvc.lock` | produit par `dvc repro` |

## Problèmes courants

- **`ssh is supported, but requires 'dvc-ssh'`** : DVC installé sans les extras. Réinstaller avec `"dvc[ssh,s3]"`.
- **Passphrase demandée à chaque commande** : `ssh-add` n'a pas été lancé dans ce terminal.
- **Erreur d'identifiants AWS** : session SSO expirée, relancer `aws sso login`.
- **`dvc: command not found`** : `~/.local/bin` n'est pas dans le `PATH` (ouvrir un nouveau terminal).
- **`missing cache` ou fichier introuvable au `pull`** : la personne qui a modifié les données n'a pas fait `dvc push`. Lui demander, ou essayer l'autre stockage avec `-r`.
- **Fichier supprimé par erreur** : `dvc checkout`.

## À savoir

- Sur la VM de préproduction, un clone peut lire le dossier directement, sans SSH : `dvc remote modify --local preprod url /var/lib/enervision/dvc`. Ne pas travailler dans `/opt/enervision`, que le minuteur de déploiement réinitialise toutes les 2 minutes.
- L'instance EC2 de production n'a que la lecture sous `dvc/` ; l'envoi se fait depuis les postes. Tous les membres ont aujourd'hui `AdministratorAccess`, donc les droits d'écriture ne sont pas un obstacle.
- `terraform destroy` vide le bucket (`force_destroy`) : les données de `prod` se renvoient depuis `preprod` ou depuis un poste.
- Sur la VM de préproduction, tous les membres utilisent le compte root pour l'instant : la clé de chacun est à ajouter dans `authorized_keys`.
