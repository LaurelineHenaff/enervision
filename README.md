# enervision
Projet Piscine EADL

EnerVision vend de l’optimisation énergétique à des industriels européens soumis à trois pressions : des prix de l’énergie volatils, un reporting extra-financier qui se durcit, et une demande interne de pilotage fin.

Technos utilisées :

- **Base de données** : PostgreSQL 16 + TimescaleDB
- **API** : FastAPI (Python 3.13)
- **Frontend** : Angular 22 (avec SSR)

## Environnement de développement

Le développement se fait sous Windows avec WSL2 et Docker Desktop. La base de données tourne dans un conteneur, et tous les membres de l'équipe utilisent la même image et la même configuration. 
Ceci permet une isométrie avec la VM Debian commune qui sert d'environnement à la pré-prod & production.

### 1. Installer les prérequis (Ne pas oublier GPUPDATE /FORCE)

- **WSL2** : utilise EniLauncher pour passer en mode WSL. Redémarre si demandé, puis ouvre un terminal PowerShell et lance :
  ```powershell
  wsl --install -d Debian
  ```
- **Docker Desktop** : ouvre-le, puis dans **Settings > Resources > WSL integration**, active la distribution WSL utilisée (Debian).

### 2. Cloner le projet

Clone le dépôt dans le système de fichiers WSL (plus rapide que `/mnt/c`) :

```bash
sudo apt install git
git clone https://github.com/LaurelineHenaff/enervision.git ~/projects/enervision
cd ~/projects/enervision
```

### 3. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Les valeurs par défaut de `.env.example` conviennent au développement local. Le fichier `.env` n'est pas versionné.

### 4. Démarrer la base de données

Depuis la racine du projet, ouvrir un nouveau terminal :

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

### 4 bis. Démarrer l'API

`docker compose up -d` démarre aussi l'API FastAPI (service `api`), une fois la base `healthy`. Le code de `api/` est monté dans le conteneur, et Uvicorn recharge l'API à chaque modification.

- Documentation interactive : http://localhost:8000/docs
- Santé du mock : http://localhost:8000/health

Après une modification de `api/requirements.txt`, reconstruis l'image :

```bash
docker compose up -d --build api
```

Logs de l'API :

```bash
docker compose logs -f api
```

L'URL du mock se règle avec `API_MOCK_URL` dans `.env`. Dans le conteneur, la base est joignable via `DATABASE_URL` (hôte `db`).

### 4 ter. Démarrer le frontend

`docker compose up -d` démarre aussi le frontend Angular (service `frontend`) avec le serveur de développement. Le code de `frontend/` est monté dans le conteneur, et la page se recharge à chaque modification. Les `node_modules` restent dans le conteneur.

- Application : http://localhost:4200

Après une modification de `frontend/package.json`, reconstruis l'image :

```bash
docker compose up -d --build frontend
```

Logs du frontend :

```bash
docker compose logs -f frontend
```

Le rendu SSR d'Angular n'accepte que les hôtes listés dans `NG_ALLOWED_HOSTS` (par défaut `localhost` et `127.0.0.1`).

### 5. Créer l'environnement Python

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
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

## Modules

### Module API
- Se connecte à la BDD TimescaleDB
- Donne accès au front avec des web services permettant de récupérer les prédictions de pics de consommation, l'historique des données et les recommandations
- Gestion de l'authentification

### Module Docs
- Donne accès à la documentation du projet

### Module ETL
- Récupère données de l'API Mock et les stocke dans BDD PostgreSQL
- Se connecte à la BDD PostgreSQL, transforme les données et les stocke dans une BDD TimescaleDB

### Module Frontend
- Se connecte à l'API
- Affiche avec dashboard prédictions, historiques des données, recommandations

### Module Infra

### Module ML
- Se connecte à la BDD TimescaleDB
- Création d'un modèle, entraînement avec données BDD TimescaleDB