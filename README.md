# enervision
Projet Piscine EADL

EnerVision vend de l’optimisation énergétique à des industriels européens soumis à trois pressions : des prix de l’énergie volatils, un reporting extra-financier qui se durcit, et une demande interne de pilotage fin.

Technos utilisées :

PostgreSQL 16 + TimescaleDB

FastAPI

React + Vite
coucou
Je suis aussi là

## Installation pas à pas (Windows + WSL)

Le développement se fait dans WSL (Debian), avec PyCharm sur Windows.

### 1. Installer WSL

Dans PowerShell (en administrateur) :

```powershell
wsl --install
```

Redémarre le PC si demandé, puis ouvre Debian et crée ton utilisateur Linux.

### 2. Préparer Debian

Dans le terminal Debian :

```bash
sudo apt update && sudo apt install -y git curl python3-venv python3-pip podman podman-compose
```

### 3. Configurer Podman

Podman remplace Docker Desktop. Dans WSL, crée la configuration suivante pour utiliser le gestionnaire de cgroups `cgroupfs` :

```bash
mkdir -p ~/.config/containers
printf '[engine]\ncgroup_manager = "cgroupfs"\n' > ~/.config/containers/containers.conf
```

### 4. Cloner le projet dans WSL

Clone le projet dans le système de fichiers Linux (plus rapide que `/mnt/c`) :

```bash
git clone https://github.com/LaurelineHenaff/enervision.git ~/projects/enervision
cd ~/projects/enervision
```

### 5. Démarrer la base de données

Depuis la racine du projet :

```bash
podman-compose up -d
```

Vérifie que le conteneur tourne :

```bash
podman ps
```

Vérifie que TimescaleDB est chargé :

```bash
podman exec -it enervision-db psql -U postgres -c "SELECT extname, extversion FROM pg_extension;"
```

La ligne `timescaledb` doit apparaître dans la liste.

### 6. Créer l'environnement Python

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 7. Configurer PyCharm

1. Ouvre le dossier `\\wsl$\Debian\home\<ton_utilisateur>\projects\enervision` dans PyCharm.
2. Va dans **Settings > Project > Python Interpreter > Add Interpreter > On WSL** et choisis `~/projects/enervision/.venv/bin/python`.
3. Dans la vue **Database**, ajoute une source PostgreSQL :
   - Host : l'IP de WSL (`ip -4 addr show eth0 | grep inet` dans Debian). Elle peut changer au redémarrage. `localhost` ne fonctionne pas depuis Windows.
   - Port : `5432`
   - Utilisateur : `postgres`
   - Mot de passe : `dev`
   - Base : `enervision`

### Arrêter la base

```bash
podman-compose down
```

Les données restent dans le volume `pgdata`.
