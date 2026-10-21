# enervision
Projet Piscine EADL

EnerVision vend de l’optimisation énergétique à des industriels européens soumis à trois pressions : des prix de l’énergie volatils, un reporting extra-financier qui se durcit, et une demande interne de pilotage fin.

Technos utilisées :

- **Base de données** : PostgreSQL 16 + TimescaleDB
- **API** : FastAPI (Python 3.13)
- **Frontend** : Angular 22 (avec SSR), Node 24

Versions communes à toute la chaîne (images Docker, CI GitHub Actions, poste de développement) : **Python 3.13** pour `api`, `etl` et `ml`, **Node 24** (24.15 minimum) pour `frontend`. Toute montée de version se change aux trois endroits : `Dockerfile`, `.github/workflows/ci.yml` et ce README.

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
git clone https://github.com/projet-piscine-eadl-enervision/enervision.git ~/projects/enervision
cd ~/projects/enervision
```

### 3. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Les valeurs par défaut de `.env.example` conviennent au développement local, sauf les trois variables du mock, à renseigner : `MOCK_API_URL`, `MOCK_API_USERNAME` et `MOCK_API_PASSWORD` (URL publique `https://api-mock.charlieandre.fr/` ou interne `http://10.43.43.80:8000`, identifiants dans les notes Teams). Le fichier `.env` n'est pas versionné : ne jamais y mettre de secret dans un fichier suivi par Git.

Ces variables s'appelaient auparavant `API_MOCK_URL`, `API_MOCK_USER` et `API_MOCK_PASSWORD`. Si votre `.env` date d'avant ce renommage, renommez-les, sinon l'API appelle le mock sans authentification (erreur 401).

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

Après une modification de `api/requirements.in`, reconstruis l'image :

```bash
docker compose up -d --build api
```

Logs de l'API :

```bash
docker compose logs -f api
```

L'URL du mock se règle avec `MOCK_API_URL` dans `.env`. Dans le conteneur, la base est joignable via `DATABASE_URL` (hôte `db`).

### 4 ter. Démarrer le frontend

`docker compose up -d` démarre aussi le frontend Angular (service `frontend`) avec le serveur de développement. Le code de `frontend/` est monté dans le conteneur, et la page se recharge à chaque modification. Les `node_modules` restent dans le conteneur.

- Application : http://localhost:4000

Après une modification de `frontend/package.json`, reconstruis l'image :

```bash
docker compose up -d --build frontend
```

Logs du frontend :

```bash
docker compose logs -f frontend
```

Le rendu SSR d'Angular n'accepte que les hôtes listés dans `NG_ALLOWED_HOSTS` (par défaut `localhost` et `127.0.0.1`).

`frontend/Dockerfile` a deux usages. En local, `docker-compose.yml` utilise l'étape `dev` (serveur de développement). La CI construit l'étape finale `prod` : l'application compilée, servie par le serveur SSR Node sur le port 4000. C'est la même image en staging et en production, donc rien qui dépend de l'environnement n'est fixé à la construction. Deux variables sont lues au lancement :

- `NG_ALLOWED_HOSTS` : nom ou IP sous lesquels le site est joint (celle de la VM en staging, l'adresse AWS en production).
- `API_UPSTREAM` : adresse de l'API (`http://api:8000` par défaut). Le front appelle l'API par un chemin relatif (`/api/...`) et le serveur (`frontend/src/api-proxy.ts`) transmet la requête à cette adresse. **Dans le code du front, toujours utiliser `/api/...`, jamais une URL complète** : elle ne serait valable que dans un seul environnement.

Pour tester l'image de production en local, avec l'API lancée par `docker compose up -d` :

```bash
docker build -t enervision-frontend-prod ./frontend
docker run --rm -p 4100:4000 -e API_UPSTREAM=http://host.docker.internal:8000 --add-host=host.docker.internal:host-gateway enervision-frontend-prod
```

Puis ouvre http://localhost:4100 (l'API est jointe par http://localhost:4100/api/health).

### 4 quater. Démarrer l'ETL

`docker compose up -d` démarre aussi l'ETL (service `etl`). Le code de `etl/` est monté dans le conteneur, et Uvicorn recharge l'ETL à chaque modification. Il lit `MOCK_API_URL`, `MOCK_API_USERNAME` et `MOCK_API_PASSWORD` dans le `.env` à la racine du projet.

- Documentation interactive : http://localhost:8001/docs

Après une modification de `etl/requirements.in`, reconstruis l'image :

```bash
docker compose up -d --build etl
```

Logs de l'ETL :

```bash
docker compose logs -f etl
```

### 4 quinquies. MLflow et le module ML

`docker compose up -d` démarre aussi le serveur MLflow (service `mlflow`, image officielle). Il enregistre les expériences, les runs et les modèles du module ML.

- Interface MLflow : http://localhost:5000
- Les données (base SQLite et artefacts) sont dans le volume Docker `mlflow-data` : elles survivent à `docker compose down`, mais pas à `docker compose down -v`.

Le service `ml` contient le code d'entraînement. Ce n'est pas un serveur : il fait son travail puis s'arrête. Il ne démarre pas avec `docker compose up -d` (profil `ml`) : lance-le à la demande :

```bash
docker compose run --rm ml
```

Cette commande démarre au besoin la base et MLflow, attend qu'ils soient prêts, puis enregistre un run dans l'expérience `enervision`, visible dans l'interface MLflow. Pour l'instant, `ml/train.py` vérifie seulement la connexion à la base et à MLflow.

Le code de `ml/` est monté dans le conteneur : une modification de `train.py` est prise en compte au lancement suivant, sans reconstruire l'image. Après une modification de `ml/requirements.in`, régénère `ml/requirements.txt`, puis reconstruis l'image :

```bash
docker compose build ml
```

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

## Staging

Le staging est déployé automatiquement sur la VM de l'école : à chaque merge sur `main` dont la CI est verte, l'image Docker de l'API est publiée sur GHCR, puis la VM la tire toutes les 2 minutes et relance les conteneurs.

- API du staging : http://10.43.43.50:8000/docs (réseau de l'école)
- Version déployée : http://10.43.43.50:8000/health (titre du commit et sha court)

Le détail (principe, mise en place de la VM, jeton GHCR, dépannage, retour arrière) est dans [`docs/deploiement-staging.md`](docs/deploiement-staging.md).

## Dépendances Python 
TODO - Rajouter `ml/` à la liste du script une fois le module créé.
Chaque module Python (`api/`, `etl/`) a deux fichiers :

- `requirements.in` : les dépendances directes, sans version figée. **C'est le seul fichier à modifier.**
- `requirements.txt` : toutes les dépendances avec leur version exacte, généré à partir du `.in`. Il est utilisé par les Dockerfiles et la CI. **Ne pas le modifier à la main.**

Après une modification d'un `requirements.in`, régénère les `requirements.txt` depuis WSL :

```bash
./infra/scripts/compile-requirements.sh
```

Pour mettre à jour une dépendance, ou toutes :

```bash
./infra/scripts/compile-requirements.sh --upgrade-package fastapi
./infra/scripts/compile-requirements.sh --upgrade
```

Commite ensuite le `.in` et le `.txt` ensemble, puis reconstruis les images (`docker compose up -d --build`). Le script gère aussi les `requirements-dev.in` s'ils existent.

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
- Enregistre les runs et les modèles dans MLflow (service `mlflow`), où l'API récupère le modèle `champion`