# enervision
Projet Piscine EADL

EnerVision vend de l’optimisation énergétique à des industriels européens soumis à trois pressions : des prix de l’énergie volatils, un reporting extra-financier qui se durcit, et une demande interne de pilotage fin.

Technos utilisées :

PostgreSQL 16 + TimescaleDB

FastAPI

React + Vite
coucou
Je suis aussi là

## Environnement de développement

Le développement se fait sous Windows avec WSL2 et Docker Desktop. La base de données tourne dans un conteneur, et tous les membres de l'équipe utilisent la même image et la même configuration. La VM Debian commune sert uniquement à la production.

### 1. Installer les prérequis

- **WSL2** : dans PowerShell (en administrateur) :
  ```powershell
  wsl --install
  ```
  Redémarre si demandé, puis ouvre la distribution Linux et crée ton utilisateur.
- **Docker Desktop** : installe-le, puis dans **Settings > Resources > WSL integration**, active la distribution WSL utilisée.
- **PyCharm** (ou un autre IDE) : installe-le sous Windows.

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
