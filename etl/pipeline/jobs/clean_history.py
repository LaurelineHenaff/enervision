"""Traitement : nettoie l'historique fourni par l'école et écrit le parquet.

Usage, depuis etl/ : python -m pipeline clean-history [--input CSV] [--output PARQUET]
"""
import argparse
import logging
from pathlib import Path

import pandas as pd

from pipeline.cleaning import CONSUMPTION_COL, WEATHER_COLS, clean

logger = logging.getLogger(__name__)

PIPELINE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PIPELINE_DIR / "provided_files" / "all_sites_combined.csv"
DEFAULT_OUTPUT = PIPELINE_DIR / "edited_files" / "energy_consumption_cleaned.parquet"


def summarize(df: pd.DataFrame) -> None:
    for col in [CONSUMPTION_COL, *WEATHER_COLS]:
        if f"{col}_source" in df:
            logger.info("%s : %s", col, df[f"{col}_source"].value_counts().to_dict())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Lecture de %s", args.input)
    cleansed = clean(pd.read_csv(args.input))
    summarize(cleansed)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    cleansed.to_parquet(args.output, engine="pyarrow", index=False)
    logger.info("%d lignes écrites dans %s", len(cleansed), args.output)
