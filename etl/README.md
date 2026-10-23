# ETL

Lit l'API Mock, nettoie l'historique 2023-2024 et, plus tard, alimentera TimescaleDB. Seule la route `/health` répond (sonde Docker et supervision).

## Installation

```bash
cd etl
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\Activate
pip install -r requirements-dev.txt
```

Variables dans un `.env` (dans `etl/` ou à la racine) : `MOCK_API_URL`, `MOCK_API_USERNAME`, `MOCK_API_PASSWORD`.

- Réseau de l'école : `MOCK_API_URL=http://10.43.43.80:8000`, identifiants vides. C'est la valeur par défaut.
- Internet : `https://api-mock.charlieandre.fr` avec l'authentification basique (notes Teams). Un 401 signifie que l'identifiant ou le mot de passe est refusé.

## Tester en local

Depuis `etl/`, environnement virtuel activé.

```bash
python -m pytest && ruff check .          # tests et lint, sans réseau ni base, moins d'une seconde
dvc pull && python -m pipeline.clean_history --output /tmp/essai.parquet   # nettoyage sur le vrai fichier
docker build -t etl-local . && docker run -d --rm --name etl-local -p 8001:8000 etl-local
docker inspect --format '{{.State.Health.Status}}' etl-local               # healthy après environ 30 s
docker rm -f etl-local
```

Client du mock, depuis le réseau de l'école :

```bash
python -c "import asyncio; from mock_client.services import site_service as s; print(asyncio.run(s.get_all_sites()))"
```

Pile complète : `docker compose up -d` à la racine, puis `docker ps` doit montrer `enervision-etl` en `healthy` (http://localhost:8001/health). `/docs` et `/sites` renvoient 404 : c'est voulu.

## Organisation

- `mock_client/client.py` : client HTTP unique (URL, authentification facultative, délai).
- `mock_client/services/` : une fonction par endpoint du mock. Elles lèvent `httpx2.HTTPStatusError` ou `httpx2.RequestError`, à l'appelant de décider. Les horodatages envoyés doivent porter un fuseau (convertis en UTC).
- `mock_client/schemas/` : réponses du mock, vérifiées sur ses réponses réelles.
- `pipeline/clean_history.py` : nettoyage de l'historique, règles dans sa docstring.
- `pipeline/provided_files/`, `pipeline/edited_files/` : données suivies par DVC, voir [`docs/donnees-dvc.md`](../docs/donnees-dvc.md).

## Nettoyage de l'historique

`dvc repro` (ou `python -m pipeline.clean_history`). Chaque colonne brute est conservée, avec `<colonne>_clean` et `<colonne>_source` (`measured`, `recovered_from_euros`, `interpolated`, `missing`). Sur le fichier actuel, pour la consommation : 119 807 mesurées, 353 retrouvées par les euros (0,15 €/kWh), 1 072 interpolées, 1 415 vides. Les 1 792 zéros sont de vraies coupures et sont conservés.
