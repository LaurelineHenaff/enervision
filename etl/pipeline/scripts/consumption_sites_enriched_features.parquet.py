import json
import logging
from pathlib import Path

import pandas as pd

# Racine absolue du projet ("pipeline")
BASE_DIR = Path(__file__).resolve().parent.parent

# Instancier le logger du module
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Paramètres d'imputation -------------------------------------------------
MAX_GAP_KWH = 4  # trous <= 4 h : interpolation linéaire ; au-delà : profil typique
MAX_GAP_WEATHER = 6  # idem pour la météo
TREAT_ZEROS_AS_MISSING = False  # True = considérer les 0 kWh comme des pannes à imputer

MEASURE_KWH = "consumption_kwh"
EUROS = "consumption_euros"
WEATHER_COLS = ["temperature_celsius", "humidity_percent", "solar_irradiance_wm2"]


def load_data(csv_path: str, json_path: str) -> tuple[pd.DataFrame, dict]:
    """Extrait les séries temporelles et les métadonnées associées."""
    logger.info(f"Extraction des données depuis {csv_path} et {json_path}...")
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    with open(json_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return df, metadata


def apply_imputation_strategies(df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
    """Applique les règles d'imputation selon les types d'incidents (bruit, pannes, maintenance)."""
    logger.info("Application des stratégies de nettoyage et d'imputation...")
    d = df.copy()

    # 1. Tri chronologique par site
    d = d.sort_values(by=["site_id", "timestamp"]).reset_index(drop=True)

    # Colonnes de mesures
    measure_cols = [
        "consumption_kwh",
        "temperature_celsius",
        "humidity_percent",
        "solar_irradiance_wm2",
    ]

    # 2. Imputation du bruit résiduel et pannes courtes par interpolation
    logger.info(
        "Interpolation linéaire pour le bruit résiduel et pannes capteurs courtes..."
    )
    for col in measure_cols:
        if col in d.columns:
            d[col] = d.groupby("site_id")[col].transform(
                lambda group: group.interpolate(
                    method="linear", limit=4, limit_direction="both"
                )
            )

    # 3. Traitement des pannes majeures et reconstruction
    logger.info("Remplissage des NaN persistants (pannes majeures/perte réseau)...")

    # Définition du tarif (ajuste selon ton besoin)
    tarif = 0.20

    # Reconstruction des kWh à partir des euros si possible
    if "consumption_kwh" in d.columns and "consumption_euros" in d.columns:
        recover = d["consumption_kwh"].isna() & d["consumption_euros"].notna()
        d.loc[recover, "consumption_kwh"] = d.loc[recover, "consumption_euros"] / tarif
        d.loc[recover, "kwh_source"] = "recovered_from_euros"

        logger.info(f"kWh reconstruits depuis les euros : {recover.sum()}")
        if "kwh_source" in d.columns:
            logger.info(
                "Origine des kWh :\n" + d["kwh_source"].value_counts().to_string()
            )

    # Remplissage par 0 pour la consommation restante en cas de coupure avérée
    if "consumption_kwh" in d.columns:
        d["consumption_kwh"] = d["consumption_kwh"].fillna(0.0)

    # Propagation pour la partie financière
    if "consumption_euros" in d.columns:
        d["consumption_euros"] = d.groupby("site_id")["consumption_euros"].ffill()

    # Contrôle des NaN restants
    for col in d.columns:
        n = int(d[col].isna().sum())
        if n:
            logger.warning(f"{n} NaN restants dans {col}")

    return d


def save_cleansed_data(df: pd.DataFrame, output_path: str):
    """Charge le DataFrame nettoyé dans le format de destination (Silver layer)."""
    logger.info(f"Chargement des données nettoyées vers {output_path}...")
    if output_path.endswith(".parquet"):
        df.to_parquet(output_path, engine="pyarrow", index=False)
    else:
        df.to_csv(output_path, index=False)
    logger.info("Pipeline terminée avec succès.")


if __name__ == "__main__":
    CSV_INPUT = str(BASE_DIR / "provided_files" / "all_sites_combined.csv")
    JSON_INPUT = str(BASE_DIR / "provided_files" / "dataset_metadata.json")
    SILVER_OUTPUT = str(
        BASE_DIR / "edited_files" / "energy_consumption_cleaned.parquet"
    )

    raw_df, meta_data = load_data(CSV_INPUT, JSON_INPUT)
    cleansed_df = apply_imputation_strategies(raw_df, meta_data)
    save_cleansed_data(cleansed_df, SILVER_OUTPUT)

    df_check = pd.read_parquet(SILVER_OUTPUT)
    print(df_check["site_id"].value_counts())
    print(df_check["kwh_source"].value_counts())
