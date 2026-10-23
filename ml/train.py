"""Point d'entrée du module ML : entraînement des modèles EnerVision.

Pour l'instant, le script vérifie seulement l'environnement : il se connecte à la base,
puis enregistre un run de test dans MLflow. Le vrai entraînement viendra ensuite.
"""

import os

import mlflow
import psycopg
from dotenv import load_dotenv

EXPERIENCE = "enervision"


def verifier_base(database_url: str) -> None:
    """Vérifie que la base répond à une requête simple."""
    with psycopg.connect(database_url, connect_timeout=10) as connexion:
        connexion.execute("SELECT 1").fetchone()


def main() -> None:
    """Vérifie la base, puis logge un run de vérification dans MLflow."""
    load_dotenv()
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    database_url = os.environ["DATABASE_URL"]

    verifier_base(database_url)
    print("Base de données : connexion OK")

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(EXPERIENCE)
    with mlflow.start_run(run_name="verification-environnement") as run:
        mlflow.log_param("version_code", os.getenv("GIT_SHA", "dev"))
        mlflow.log_metric("base_accessible", 1.0)

    print(
        f"MLflow : run {run.info.run_id} enregistré dans l'expérience '{EXPERIENCE}' ({tracking_uri})"
    )


if __name__ == "__main__":
    main()
