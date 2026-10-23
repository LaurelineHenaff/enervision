"""Configuration de pytest : variables d'environnement factices, requises à l'import de app.core.config."""
import os

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "cle-de-test")
