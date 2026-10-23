"""Nettoyage des relevés historiques 2023-2024 (couche silver).

Source : all_sites_combined.csv (7 sites, un relevé par heure), suivi avec DVC. Les colonnes brutes
sont conservées, NULL compris ; la valeur nettoyée est écrite à côté (<colonne>_clean) avec son
origine (<colonne>_source).

Règles, mesurées sur le fichier :
- horodatages en UTC (le fichier n'a aucun fuseau : sans fuseau = UTC, comme l'API Mock) ;
- zéros de consommation conservés : ce sont de vraies coupures (euros aussi à 0) ;
- kWh manquant avec montant connu : montant / 0,15 (rapport mesuré de 0,1496 à 0,1503) ;
- trou de 4 h au plus (6 h pour la météo) : interpolation linéaire ; au-delà, laissé vide.

Usage, depuis etl/ : python -m pipeline.clean_history [--input CSV] [--output PARQUET]
"""
import argparse
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PIPELINE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = PIPELINE_DIR / "provided_files" / "all_sites_combined.csv"
DEFAULT_OUTPUT = PIPELINE_DIR / "edited_files" / "energy_consumption_cleaned.parquet"

TARIFF_EUR_PER_KWH = 0.15
MAX_GAP_KWH = 4  # heures
MAX_GAP_WEATHER = 6  # heures

CONSUMPTION_COL = "consumption_kwh"
EUROS_COL = "consumption_euros"
WEATHER_COLS = ["temperature_celsius", "humidity_percent", "solar_irradiance_wm2"]

SOURCE_MEASURED = "measured"
SOURCE_RECOVERED = "recovered_from_euros"
SOURCE_INTERPOLATED = "interpolated"
SOURCE_MISSING = "missing"


def load_data(csv_path: Path) -> pd.DataFrame:
    logger.info("Lecture de %s", csv_path)
    return pd.read_csv(csv_path)


def normalize_timestamps(timestamps: pd.Series) -> pd.Series:
    """Ramène des horodatages ISO 8601, avec ou sans fuseau, en UTC (sans fuseau = UTC)."""
    return pd.to_datetime(timestamps, utc=True, format="ISO8601")


def interpolate_short_gaps(values: pd.Series, max_gap: int) -> pd.Series:
    """Interpole linéairement uniquement les trous de `max_gap` valeurs au plus.

    Contrairement à interpolate(limit=N), qui remplit les N premières valeurs d'un long trou et
    laisse le reste vide, un trou trop long reste ici entièrement vide. Les bords ne sont pas
    extrapolés.
    """
    filled = values.interpolate(method="linear", limit_area="inside")
    gap_length = values.isna().groupby(values.notna().cumsum()).transform("sum")
    return filled.mask(values.isna() & (gap_length > max_gap))


def _fill(df: pd.DataFrame, col: str, max_gap: int, fallback: pd.Series | None = None) -> None:
    """Ajoute <col>_clean et <col>_source ; `fallback` donne une valeur de repli aux manquants."""
    raw = df[col]
    clean = raw.copy()
    source = pd.Series(SOURCE_MEASURED, index=df.index)

    if fallback is not None:
        recovered = raw.isna() & fallback.notna()
        clean[recovered] = fallback[recovered]
        source[recovered] = SOURCE_RECOVERED

    still_missing = clean.isna()
    clean = clean.groupby(df["site_id"]).transform(lambda s: interpolate_short_gaps(s, max_gap))
    source[still_missing & clean.notna()] = SOURCE_INTERPOLATED
    source[clean.isna()] = SOURCE_MISSING

    df[f"{col}_clean"] = clean
    df[f"{col}_source"] = source


def clean(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["timestamp"] = normalize_timestamps(d["timestamp"])

    duplicates = int(d.duplicated(["site_id", "timestamp"]).sum())
    if duplicates:
        logger.warning("%d doublons (site, horodatage) supprimés, le premier est gardé", duplicates)
        d = d.drop_duplicates(["site_id", "timestamp"], keep="first")
    d = d.sort_values(["site_id", "timestamp"]).reset_index(drop=True)

    # L'interpolation compte des lignes : elle suppose un relevé par heure sans ligne absente
    irregular = int((d.groupby("site_id")["timestamp"].diff().dropna() != pd.Timedelta("1h")).sum())
    if irregular:
        logger.warning("%d intervalles différents d'une heure : les trous peuvent être sous-estimés", irregular)

    euros = d[EUROS_COL] / TARIFF_EUR_PER_KWH if EUROS_COL in d else None
    _fill(d, CONSUMPTION_COL, MAX_GAP_KWH, fallback=euros)
    for col in WEATHER_COLS:
        if col in d:
            _fill(d, col, MAX_GAP_WEATHER)
    return d


def summarize(df: pd.DataFrame) -> None:
    for col in [CONSUMPTION_COL, *WEATHER_COLS]:
        if f"{col}_source" in df:
            counts = df[f"{col}_source"].value_counts().to_dict()
            logger.info("%s : %s", col, counts)


def save_cleansed_data(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, engine="pyarrow", index=False)
    logger.info("%d lignes écrites dans %s", len(df), output_path)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    cleansed = clean(load_data(args.input))
    summarize(cleansed)
    save_cleansed_data(cleansed, args.output)


if __name__ == "__main__":
    main()
