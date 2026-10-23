# ETL

Le module lit l'API Mock, nettoie l'historique 2023-2024 et, plus tard, alimentera TimescaleDB. Il n'expose pas d'API métier : seule la route `/health` répond (sonde Docker et supervision).

## Installation

```bash
cd etl
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\Activate
pip install -r requirements-dev.txt
```

Créer un fichier `.env` dans `etl/` avec `MOCK_API_URL`, `MOCK_API_USERNAME` et `MOCK_API_PASSWORD`. Sur le réseau de l'école, `MOCK_API_URL` vaut par défaut `http://10.43.43.80:8000` et les identifiants sont inutiles ; l'URL publique demande l'authentification basique.

```bash
python -m uvicorn main:app --reload     # http://localhost:8000/health
python -m pytest                        # tests unitaires, sans réseau ni base
```

Avec `docker compose up -d` (README à la racine), l'ETL est publié sur http://localhost:8001/health.

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
