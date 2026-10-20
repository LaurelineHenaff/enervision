# enervision
Projet Piscine EADL

EnerVision vend de l’optimisation énergétique à des industriels européens soumis à trois pressions : des prix de l’énergie volatils, un reporting extra-financier qui se durcit, et une demande interne de pilotage fin.

Technos utilisées :

PostgreSQL 16 + TimescaleDB

FastAPI

React + Vite


### Module API
- Se connecte à la BDD TimescaleDB
- Donne accès au front avec des web services permettant de récupérer les prédictions de pics de consommation, l'historique des données et les recommandations
- Gestion de l'authentification

### Module Docs
- Donne accès à la documentation du projet

### Module ETL
- Récupère données de l'API Mock et les stocke dans BDD PostgreSQL
- Se connecte à la BDD PostgreSQL, transforme les données et les stocke dans une BDD TimescalDB

### Module Frontend
- Se connecte à l'API
- Affiche avec dashboard prédictions, historiques des données, recommandations

### Module Infra

### Module ML
- Se connecte à la BDD TimescaleDB
- Création d'un modèle, entraînement avec données BDD TimescaleDB

## Environnement de développement

Le développement se fait sous Windows avec WSL2 et Docker Desktop. La base de données tourne dans un conteneur, et tous les membres de l'équipe utilisent la même image et la même configuration. La VM Debian commune sert uniquement à la production.

### 1. Installer les prérequis

- **WSL2** : Utiliser EniLaucnher pour passer en mode WSL.

  Redémarre si demandé, puis ouvre un terminal Powershell et run la commande :
```
wsl
```
- **Docker Desktop** : Ouvrir puis dans **Settings > Resources > WSL integration**, active la distribution WSL utilisée (Debian).

### 2. Cloner le projet

Clone le dépôt dans le système de fichiers WSL (plus rapide que `/mnt/c`) :

```bash
git clone https://github.com/LaurelineHenaff/enervision.git ~/projects/enervision
cd ~/projects/enervision
```

### 3. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Les valeurs par défaut de `.env.example` conviennent au développement local. Le fichier `.env` n'est pas versionné.

### 4. Démarrer la base de données

Depuis la racine du projet :

```bash
docker compose up -d
```

Vérifie que le conteneur est healthy :

```bash
docker compose ps
```

Vérifie que TimescaleDB est chargé :

```bash
docker compose exec db psql -U postgres -d enervision -c "SELECT extname, extversion FROM pg_extension;"
```

La ligne `timescaledb` doit apparaître dans la liste.

Arrêter la base (les données restent dans le volume `pgdata`) :

```bash
docker compose down
```

### 5. Créer l'environnement Python

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 6. Configurer PyCharm

1. Ouvre le dossier `\\wsl$\<distribution>\home\<ton_utilisateur>\projects\enervision` dans PyCharm.
2. Va dans **Settings > Project > Python Interpreter > Add Interpreter > On WSL** et choisis `~/projects/enervision/.venv/bin/python`.
3. Dans la vue **Database**, ajoute une source PostgreSQL :
   - Host : `localhost`. Si la connexion est refusée, utilise l'IP de WSL (`ip -4 addr show eth0 | grep inet` dans la distribution).
   - Port : `5432`
   - Utilisateur : `postgres`
   - Mot de passe : `dev`
   - Base : `enervision`
