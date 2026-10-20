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

- http://localhost:8000/health : vérifie que l'API Mock répond
- http://localhost:8000/docs : documentation Swagger

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
