"""Règles de nettoyage de l'historique 2023-2024 (fonctions pures, sans fichier).

Les colonnes brutes sont conservées, NULL compris ; la valeur nettoyée est écrite à côté
(<colonne>_clean) avec son origine (<colonne>_source).

Règles, mesurées sur le fichier fourni :
- horodatages en UTC (le fichier n'a aucun fuseau : sans fuseau = UTC, comme l'API Mock) ;
- zéros de consommation conservés : ce sont de vraies coupures (euros aussi à 0) ;
- kWh manquant avec montant connu : montant / 0,15 (rapport mesuré de 0,1496 à 0,1503) ;
- trou de 4 h au plus (6 h pour la météo) : interpolation linéaire ; au-delà, laissé vide ;
- anomalies étiquetées dans les métadonnées : colonnes anomaly_type et anomaly_severity ; pas
  d'interpolation dans une coupure étiquetée. Durée lue dans la description ("(5h)"), une heure
  à défaut (hypothèse pour les pics et les chutes).
"""
import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)

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

OUTAGE = "outage"


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
        problems.append(f"fréquence annoncée {metadata.get('frequency')!r}, une heure attendue")

    sites = metadata.get("sites", {})
    for site_id in sorted(set(df["site_id"]) - set(sites)):
        problems.append(f"{site_id} : absent des métadonnées")

    for site_id, site in sites.items():
        rows = df[df["site_id"] == site_id]
        if len(rows) != site["total_records"]:
            problems.append(f"{site_id} : {len(rows)} lignes, {site['total_records']} annoncées")
        if rows.empty:
            continue
        start, end = normalize_timestamps(pd.Series([site["start_date"], site["end_date"]]))
        if rows["timestamp"].min() != start or rows["timestamp"].max() != end:
            problems.append(f"{site_id} : période {rows['timestamp'].min()} à {rows['timestamp'].max()}, {start} à {end} annoncée")
    return problems


def _fill(
    df: pd.DataFrame,
    col: str,
    max_gap: int,
    fallback: pd.Series | None = None,
    no_interpolation: pd.Series | None = None,
) -> None:
    """Ajoute <col>_clean et <col>_source.

    `fallback` donne une valeur de repli aux manquants ; `no_interpolation` désigne les lignes
    où l'interpolation est interdite.
    """
    raw = df[col]
    clean = raw.copy()
    source = pd.Series(SOURCE_MEASURED, index=df.index)

    if fallback is not None:
        recovered = raw.isna() & fallback.notna()
        clean[recovered] = fallback[recovered]
        source[recovered] = SOURCE_RECOVERED

    still_missing = clean.isna()
    clean = clean.groupby(df["site_id"]).transform(lambda s: interpolate_short_gaps(s, max_gap))
    if no_interpolation is not None:
        clean = clean.mask(still_missing & no_interpolation)
    source[still_missing & clean.notna()] = SOURCE_INTERPOLATED
    source[clean.isna()] = SOURCE_MISSING

    df[f"{col}_clean"] = clean
    df[f"{col}_source"] = source


def clean(df: pd.DataFrame, metadata: dict | None = None) -> pd.DataFrame:
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

    in_outage = None
    if metadata is not None:
        d = annotate_anomalies(d, metadata)
        in_outage = (d["anomaly_type"] == OUTAGE).fillna(False).astype(bool)

    euros = d[EUROS_COL] / TARIFF_EUR_PER_KWH if EUROS_COL in d else None
    _fill(d, CONSUMPTION_COL, MAX_GAP_KWH, fallback=euros, no_interpolation=in_outage)
    for col in WEATHER_COLS:
        if col in d:
            _fill(d, col, MAX_GAP_WEATHER)
    return d
