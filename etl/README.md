# ETL

Le module lit l'API Mock, nettoie l'historique 2023-2024 et, plus tard, alimentera TimescaleDB. Il n'expose pas d'API métier : seule la route `/health` répond (sonde Docker et supervision).

## Installation

```bash
cd etl
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\Activate
pip install -r requirements-dev.txt
```

Les variables `MOCK_API_URL`, `MOCK_API_USERNAME` et `MOCK_API_PASSWORD` se lisent dans un fichier `.env`, placé dans `etl/` ou à la racine du dépôt (celui de docker compose est lu aussi).

- Sur le réseau de l'école : `MOCK_API_URL=http://10.43.43.80:8000`, identifiant et mot de passe vides. Aucune authentification n'est envoyée. Sans `MOCK_API_URL`, cette valeur est prise par défaut.
- Depuis Internet : `MOCK_API_URL=https://api-mock.charlieandre.fr`, avec l'authentification basique (identifiants dans les notes Teams). Un **401** signifie que l'identifiant ou le mot de passe est refusé, pas que le code est en cause.

Avec `docker compose up -d` (README à la racine), l'ETL est publié sur http://localhost:8001/health.

## Tester en local

Depuis `etl/`, environnement virtuel activé. Du plus rapide au plus complet.

**1. Tests unitaires et lint**, sans réseau ni base de données, moins d'une seconde :

```bash
python -m pytest
python -m pytest --cov=mock_client --cov=pipeline --cov-report=term-missing
ruff check .
```

**2. Nettoyage de l'historique** sur le vrai fichier :

```bash
dvc pull                                                  # voir docs/donnees-dvc.md
python -m pipeline.clean_history --output /tmp/essai.parquet
```

Les journaux comptent les valeurs par origine. Sur le fichier actuel : 119 807 mesurées, 353 retrouvées par les euros, 1 072 interpolées, 1 415 laissées vides pour la consommation. `dvc repro` fait la même chose dans `pipeline/edited_files/` et ne relance l'étape que si le script ou le CSV a changé.

**3. Client de l'API Mock**, depuis le réseau de l'école (voir plus haut pour l'URL) :

```bash
python - <<'EOF'
import asyncio
from mock_client.services import site_service, statistic_service

async def main():
    print([s.site_id for s in await site_service.get_all_sites()])
    print((await statistic_service.get_stats_summary()).total_consumption_kw, "kW")

asyncio.run(main())
EOF
```

**4. Image Docker et sonde de santé** :

```bash
docker build -t etl-local .
docker run -d --rm --name etl-local -p 8001:8000 etl-local
docker inspect --format '{{.State.Health.Status}}' etl-local   # "healthy" après environ 30 s
docker rm -f etl-local
```

Puis http://localhost:8001/health dans un navigateur (`/docs` et `/sites` renvoient 404 : c'est voulu).

**5. Pile complète** (base, migrations, API, ETL) : `docker compose up -d` depuis la racine, puis `docker ps` doit montrer `enervision-etl` en `healthy`.

## Organisation

| Dossier | Rôle |
|---|---|
| `mock_client/client.py` | Client HTTP unique : URL de base, authentification facultative, délai d'attente. |
| `mock_client/services/` | Une fonction par endpoint du mock (sites, relevés, alertes, capteurs, synthèse, simulation). |
| `mock_client/schemas/` | Modèles Pydantic des réponses du mock, vérifiés sur ses réponses réelles. |
| `pipeline/clean_history.py` | Nettoyage de l'historique fourni par l'école (voir ci-dessous). |
| `pipeline/provided_files/` | Fichiers fournis, suivis avec DVC (jamais dans Git). |
| `pipeline/edited_files/` | Fichiers produits par le pipeline, reconstruits par `dvc repro`. |

Les services lèvent `httpx2.HTTPStatusError` (statut 4xx ou 5xx) et `httpx2.RequestError` (réseau) : c'est à l'appelant de décider de réessayer ou de stocker l'échec. Les horodatages envoyés au mock doivent porter un fuseau et sont convertis en UTC.

## Nettoyage de l'historique

```bash
dvc pull                       # récupère les fichiers fournis (voir docs/donnees-dvc.md)
python -m pipeline.clean_history
```

ou `dvc repro`, qui ne relance l'étape que si le script ou le CSV a changé. Le script garde chaque colonne brute et ajoute `<colonne>_clean` et `<colonne>_source` (`measured`, `recovered_from_euros`, `interpolated`, `missing`). Les règles et leurs preuves sont dans la docstring du module. Sur le fichier actuel : 353 kWh retrouvés par le montant en euros (tarif de 0,15 €/kWh mesuré), 1 072 trous courts interpolés, 1 415 valeurs laissées vides, 1 792 zéros conservés comme coupures réelles.
