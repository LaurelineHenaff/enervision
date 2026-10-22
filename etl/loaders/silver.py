"""Chargement des données silver (historique nettoyé) dans core.energy_reading.

Usage, depuis etl/ (ou dans le conteneur : docker compose exec etl ...) :
    python -m loaders.silver chemin/vers/conso_energie_nettoyee.parquet

Le fichier peut être un parquet ou un CSV avec les colonnes produites par le
nettoyage (timestamp, site_id, site_type, site_name, consumption_kwh, ...).
Le chargement est relançable : une heure déjà présente pour un site est ignorée.
Les tables sont créées par les migrations de l'API (api/migrations).
"""
import argparse
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import psycopg

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "timestamp",
    "site_id",
    "site_type",
    "site_name",
    "consumption_kwh",
    "consumption_euros",
    "temperature_celsius",
    "humidity_percent",
    "solar_irradiance_wm2",
    "kwh_source",
]

# Colonnes de core.energy_reading remplies depuis le silver, dans l'ordre du COPY
READING_COLUMNS = [
    "time",
    "site_id",
    "consumption_kw",
    "consumption_kwh",
    "consumption_euros",
    "temperature_celsius",
    "humidity_percent",
    "solar_irradiance_wm2",
    "data_quality",
]


@dataclass
class LoadResult:
    read: int
    inserted: int

    @property
    def skipped(self) -> int:
        return self.read - self.inserted


def read_silver(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, parse_dates=["timestamp"])


def to_readings(df: pd.DataFrame) -> pd.DataFrame:
    """Met le silver au format de core.energy_reading."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans le fichier silver : {', '.join(missing)}")

    out = pd.DataFrame(
        {
            # Les horodatages du jeu de données n'ont pas de fuseau et ne sautent aucune
            # heure au changement d'heure : ils sont lus comme de l'UTC
            "time": pd.to_datetime(df["timestamp"], utc=True),
            "site_id": df["site_id"],
            # Pas d'une heure : la puissance moyenne en kW vaut l'énergie en kWh
            "consumption_kw": df["consumption_kwh"],
            "consumption_kwh": df["consumption_kwh"],
            "consumption_euros": df["consumption_euros"],
            "temperature_celsius": df["temperature_celsius"],
            "humidity_percent": df["humidity_percent"],
            "solar_irradiance_wm2": df["solar_irradiance_wm2"],
            "data_quality": df["kwh_source"],
        }
    )
    return out[READING_COLUMNS]


def load(df: pd.DataFrame, conninfo: str) -> LoadResult:
    readings = to_readings(df)
    sites = df[["site_id", "site_name", "site_type"]].drop_duplicates("site_id")

    with psycopg.connect(conninfo) as conn, conn.cursor() as cur:
        known = {row[0] for row in cur.execute("SELECT code FROM ref.data_quality")}
        unknown = set(readings["data_quality"].dropna()) - known
        if unknown:
            raise ValueError(f"Valeurs de kwh_source absentes de ref.data_quality : {sorted(unknown)}")

        cur.executemany(
            "INSERT INTO ref.site_type (site_type) VALUES (%s) ON CONFLICT DO NOTHING",
            [(t,) for t in sites["site_type"].unique()],
        )
        cur.executemany(
            """
            INSERT INTO ref.site (site_id, site_name, site_type) VALUES (%s, %s, %s)
            ON CONFLICT (site_id) DO UPDATE
            SET site_name = EXCLUDED.site_name, site_type = EXCLUDED.site_type
            """,
            list(sites.itertuples(index=False, name=None)),
        )

        # COPY dans une table temporaire (rapide), puis insertion sans doublon
        cur.execute(
            "CREATE TEMP TABLE silver_stage (LIKE core.energy_reading INCLUDING DEFAULTS) "
            "ON COMMIT DROP"
        )
        columns = ", ".join(READING_COLUMNS)
        with cur.copy(f"COPY silver_stage ({columns}) FROM STDIN") as copy:
            for row in readings.itertuples(index=False, name=None):
                copy.write_row([None if pd.isna(v) else v for v in row])
        cur.execute(
            f"""
            INSERT INTO core.energy_reading ({columns})
            SELECT {columns} FROM silver_stage
            ON CONFLICT (time, site_id) DO NOTHING
            """
        )
        inserted = cur.rowcount

    return LoadResult(read=len(readings), inserted=inserted)


def conninfo_from_env() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL n'est pas définie")
    # Même variable que l'API, qui peut porter le driver asynchrone
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path, help="fichier silver (.parquet ou .csv)")
    args = parser.parse_args(argv)

    df = read_silver(args.path)
    result = load(df, conninfo_from_env())
    logger.info(
        "%s : %d lignes lues, %d insérées, %d déjà présentes",
        args.path.name,
        result.read,
        result.inserted,
        result.skipped,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
