"""Métadonnées du jeu de données : anomalies étiquetées et contrôle de cohérence.

La durée d'une anomalie est lue dans sa description ("(5h)"), une heure à défaut (hypothèse pour
les pics et les chutes).
"""
import re

import pandas as pd

from pipeline.timestamps import normalize_timestamps

OUTAGE = "outage"


def _duration_hours(description: str) -> int:
    found = re.search(r"\((\d+)h\)", description)
    return int(found.group(1)) if found else 1


def annotate_anomalies(df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
    """Ajoute anomaly_type et anomaly_severity aux lignes couvertes par une anomalie étiquetée.

    `df` doit avoir des horodatages en UTC. En cas de chevauchement, la coupure l'emporte.
    """
    d = df.copy()
    d["anomaly_type"] = pd.Series(pd.NA, index=d.index, dtype="string")
    d["anomaly_severity"] = pd.Series(pd.NA, index=d.index, dtype="string")

    for site_id, site in metadata.get("sites", {}).items():
        rows = d.index[d["site_id"] == site_id]
        if rows.empty or not site.get("anomalies"):
            continue
        timestamps = d.loc[rows, "timestamp"]
        anomalies = pd.DataFrame(site["anomalies"])
        anomalies["start"] = normalize_timestamps(anomalies["timestamp"])
        anomalies["hours"] = anomalies["description"].map(_duration_hours)
        # Les coupures en dernier : elles écrasent les autres types en cas de chevauchement
        anomalies = anomalies.sort_values("type", key=lambda s: s == OUTAGE, kind="stable")
        for a in anomalies.itertuples():
            covered = (timestamps >= a.start) & (timestamps < a.start + pd.Timedelta(hours=a.hours))
            d.loc[rows[covered.to_numpy()], ["anomaly_type", "anomaly_severity"]] = [a.type, a.severity]
    return d


def check_against_metadata(df: pd.DataFrame, metadata: dict) -> list[str]:
    """Écarts entre les données (horodatages en UTC) et ce que les métadonnées annoncent."""
    problems = []
    if metadata.get("frequency") != "1h":
        problems.append(f"frequency announced {metadata.get('frequency')!r}, one hour expected")

    sites = metadata.get("sites", {})
    for site_id in sorted(set(df["site_id"]) - set(sites)):
        problems.append(f"{site_id}: absent from the metadata")

    for site_id, site in sites.items():
        rows = df[df["site_id"] == site_id]
        if len(rows) != site["total_records"]:
            problems.append(f"{site_id}: {len(rows)} rows, {site['total_records']} announced")
        if rows.empty:
            continue
        start, end = normalize_timestamps(pd.Series([site["start_date"], site["end_date"]]))
        if rows["timestamp"].min() != start or rows["timestamp"].max() != end:
            problems.append(f"{site_id}: period {rows['timestamp'].min()} to {rows['timestamp'].max()}, {start} to {end} announced")
    return problems
