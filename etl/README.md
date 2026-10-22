# ETL 

## Installation (Windows) pour se connecter à l'API Mock

```powershell
cd etl
python -m venv .venv
.venv\Scripts\Activate
python -m pip install -r requirements.txt
```

## Lancer en local

```powershell
python -m uvicorn main:app --reload
```

- http://localhost:8000/sites : liste des sites, lue depuis l'API Mock
- http://localhost:8000/docs : documentation Swagger

Avec `docker compose up -d` (voir le README à la racine), l'ETL est publié sur le port 8001 : http://localhost:8001/docs.

## Charger les données silver dans la base

`loaders/silver.py` charge l'historique nettoyé (parquet ou CSV) dans `core.energy_reading`, et remplit `ref.site` au passage. Les tables sont créées par les migrations de l'API, appliquées au démarrage du conteneur `api`.

```bash
docker compose exec etl python -m loaders.silver data/silver/conso_energie_nettoyee.parquet
```

Le chemin est relatif au dossier `etl/`, monté dans le conteneur. Le fichier silver se récupère avec `dvc pull` (voir `docs/donnees-dvc.md`, branche `dvc-s3`). Le chargement est relançable : une heure déjà présente pour un site est ignorée, et le script affiche le nombre de lignes lues, insérées et déjà présentes. Sur le fichier silver complet (122 647 lignes), compter une dizaine de secondes.

Correspondance des colonnes :

| Silver | `core.energy_reading` |
|---|---|
| `timestamp` (sans fuseau, lu en UTC) | `time` |
| `consumption_kwh` | `consumption_kwh`, et `consumption_kw` (pas d'une heure) |
| `consumption_euros`, `temperature_celsius`, `humidity_percent`, `solar_irradiance_wm2` | mêmes noms |
| `kwh_source` | `data_quality`, qui doit exister dans `ref.data_quality` |
| `site_name`, `site_type` | `ref.site`, `ref.site_type` |

Les colonnes calendaire (`hour`, `day_of_week`, `is_weekend`...) ne sont pas stockées : elles se recalculent depuis `time`.

Tests : `DATABASE_URL=postgresql://postgres:dev@localhost:5432/enervision pytest` depuis `etl/`. Sans `DATABASE_URL`, seuls les tests sans base tournent.

## Rôle de chaque couche

| Dossier | Rôle |
|---|---|
| `routers/` | Reçoit la requête HTTP, appelle un service, renvoie la réponse. Pas de logique métier. |
| `core/` | Configuration, sécurité. |
| `models/` | Données telles que stockées en base. |
| `repositories/` | Accès à la base de données. |
| `schemas/` | Modèles Pydantic des données échangées avec le front. |
| `services/` | Logique métier. |

### Fichier env
Pour que le module fonctionne, il faut créer un fichier .env à la racine du module ETL, contenant les valeurs de MOCK_API_URL, MOCK_API_USERNAME, MOCK_API_PASSWORD\
exemple : MOCK_API_USERNAME=name
