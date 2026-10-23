"""Horodatages : tout est ramené en UTC."""
import pandas as pd


def normalize_timestamps(timestamps: pd.Series) -> pd.Series:
    """Ramène des horodatages ISO 8601, avec ou sans fuseau, en UTC (sans fuseau = UTC)."""
    return pd.to_datetime(timestamps, utc=True, format="ISO8601")
