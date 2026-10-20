# API EnerVision

API REST du projet, en **FastAPI** (Python 3.13), connectée à **PostgreSQL 16 + TimescaleDB** via **SQLAlchemy 2.0** en asynchrone.

Elle gère l'authentification (JWT) et expose au front Angular les prédictions de pics, l'historique de consommation et les recommandations.

## Démarrer

L'API tourne dans Docker, avec la base. Depuis la **racine du projet** :

```bash
cp .env.example .env        # première fois seulement, puis renseigner SECRET_KEY
docker compose up -d
```

- Documentation interactive (Swagger) : http://localhost:8000/docs
- Santé de l'API : http://localhost:8000/health

> Utilise `localhost` dans le navigateur, pas `0.0.0.0`.

Le dossier `api/` est monté dans le conteneur : Uvicorn recharge l'API à chaque modification. Après un changement de `requirements.txt`, reconstruis l'image :

```bash
docker compose up -d --build api
```

Voir les logs (erreurs 500, etc.) :

```bash
docker compose logs -f api
```

## Variables d'environnement

Lues par `app/core/config.py` (pydantic-settings). L'API refuse de démarrer si une variable obligatoire manque.

| Variable | Obligatoire | Description |
|---|---|---|
| `DATABASE_URL` | oui | Fournie par `docker-compose.yml`. Doit commencer par `postgresql+asyncpg://` |
| `SECRET_KEY` | oui | Clé de signature des JWT. Générer avec `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | non | Durée de validité du jeton (défaut : `60`) |
| `ALGORITHM` | non | Algorithme JWT (défaut : `HS256`) |
| `FRONTEND_ORIGIN` | non | Origine autorisée par le CORS (défaut : `http://localhost:4200`) |

## Structure

```
api/
├── app/
│   ├── main.py            # Point d'entrée : routes, CORS, création des tables
│   ├── core/
│   │   ├── config.py      # Variables d'environnement
│   │   └── security.py    # Hachage des mots de passe, création/lecture des JWT
│   ├── db/
│   │   ├── base.py        # Classe Base dont héritent tous les modèles
│   │   └── session.py     # Connexion à la base + dépendance get_db()
│   ├── models/            # Tables SQL (SQLAlchemy) — un fichier par table
│   ├── schemas/           # Données entrantes/sortantes de l'API (Pydantic)
│   └── api/
│       ├── deps.py        # Dépendances partagées : DbSession, CurrentUser, AdminUser
│       └── routes/        # Un fichier par groupe de routes
├── tests/
├── Dockerfile
└── requirements.txt
```

**Modèle ≠ schéma** : un *modèle* (`models/`) décrit une table en base ; un *schéma* (`schemas/`) décrit ce que l'API reçoit ou renvoie. Les séparer évite par exemple d'exposer `hashed_password`.

## Routes

| Méthode | Route | Accès | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | public | Inscription (email + mot de passe ≥ 8 caractères) |
| `POST` | `/api/auth/login` | public | Connexion, renvoie un jeton JWT |
| `GET` | `/api/auth/me` | connecté | Profil de l'utilisateur courant |
| `GET` | `/api/predictions` | connecté | Prédictions de pics de consommation |
| `GET` | `/api/history?days=7` | connecté | Historique de consommation (1 à 90 jours) |
| `GET` | `/api/recommendations` | connecté | Recommandations d'optimisation |
| `GET` | `/health` | public | Vérifie que l'API répond |

> Les routes `predictions`, `history` et `recommendations` renvoient pour l'instant des **données d'exemple** (voir les `TODO`).

### Tester dans Swagger

1. Ouvre http://localhost:8000/docs
2. `POST /api/auth/register` → **Try it out** → renseigne email et mot de passe → **Execute**
3. **Authorize** (en haut à droite) → email dans *username*, puis mot de passe
4. Les routes protégées répondent maintenant `200` (sinon `401`)

## Authentification et rôles

- Les mots de passe sont **hachés** (bcrypt), jamais stockés en clair.
- Le jeton s'envoie dans l'en-tête `Authorization: Bearer <jeton>`.
- Chaque utilisateur a un rôle : `user` (par défaut) ou `admin`.

Protéger une route dans `app/api/routes/` :

```python
from app.api.deps import AdminUser, CurrentUser, DbSession

@router.get("/exemple")
async def exemple(current_user: CurrentUser, db: DbSession):  # connecté → sinon 401
    ...

@router.get("/admin/exemple")
async def admin_exemple(admin: AdminUser, db: DbSession):     # admin → sinon 403
    ...
```

On ne devient **jamais** admin via l'API (`role` n'est pas accepté à l'inscription). Pour promouvoir un compte :

```bash
docker compose exec db psql -U postgres -d enervision \
  -c "UPDATE users SET role = 'admin' WHERE email = 'toi@mail.com';"
```

## Base de données

Ouvrir un terminal SQL :

```bash
docker compose exec db psql -U postgres -d enervision
```

```sql
\dt                     -- lister les tables
\d users                -- structure de la table users
SELECT * FROM users;
\q                      -- quitter
```

### Ajouter une table

1. Créer `app/models/ma_table.py` avec une classe qui hérite de `Base` et définit `__tablename__`.
2. L'importer dans `app/main.py` (à côté de `from app.models import user`), sinon elle n'est pas créée.
3. Redémarrer l'API : la table est créée au démarrage.

> ⚠️ `create_all` crée les tables **absentes** mais ne modifie **jamais** une table existante. Après l'ajout d'une colonne, en dev, supprimer la table (`DROP TABLE ma_table;`) pour qu'elle soit recréée. En production, on passera par des migrations **Alembic**.

## Notes techniques

- **Asynchrone** : les routes sont en `async def` et la base est interrogée avec `await`. Ne pas oublier `await` devant les appels à `db`.
- **Commit** : `get_db()` ne valide rien automatiquement — une route qui écrit doit appeler `await db.commit()`. En cas d'erreur, tout ce qui n'est pas commité est annulé.
- **bcrypt est figé en `4.0.1`** dans `requirements.txt` : `passlib` n'est plus maintenu et plante avec les versions plus récentes de bcrypt.
