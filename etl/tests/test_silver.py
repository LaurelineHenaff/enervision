"""Tests du chargement silver. Les tests marqués db demandent une base migrée (DATABASE_URL)."""
import os

import pandas as pd
import psycopg
import pytest

from loaders.silver import conninfo_from_env, load, main, to_readings

SITE = "TEST_SILVER"


def silver_rows(hours: int = 3) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2023-01-01", periods=hours, freq="h"),
            "site_id": SITE,
            "site_type": "office",
            "site_name": "Site de test",
            "consumption_kwh": [10.0, None, 12.5][:hours],
            "consumption_euros": [1.5, 1.6, 1.875][:hours],
            "temperature_celsius": 10.0,
            "humidity_percent": 70.0,
            "solar_irradiance_wm2": 0.0,
            "kwh_source": ["observed", "interpolated", "recovered_from_euros"][:hours],
        }
    )


def test_to_readings_maps_columns():
    out = to_readings(silver_rows())

    assert list(out.columns)[:2] == ["time", "site_id"]
    assert str(out["time"].dt.tz) == "UTC"
    assert out["consumption_kw"].iloc[0] == 10.0
    assert out["data_quality"].tolist() == ["observed", "interpolated", "recovered_from_euros"]


def test_to_readings_rejects_missing_columns():
    with pytest.raises(ValueError, match="kwh_source"):
        to_readings(silver_rows().drop(columns="kwh_source"))


needs_db = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL absente")


@pytest.fixture
def conninfo():
    info = conninfo_from_env()
    yield info
    with psycopg.connect(info) as conn:
        conn.execute("DELETE FROM core.energy_reading WHERE site_id = %s", (SITE,))
        conn.execute("DELETE FROM ref.site WHERE site_id = %s", (SITE,))


@needs_db
def test_load_twice_does_not_duplicate(conninfo):
    first = load(silver_rows(), conninfo)
    second = load(silver_rows(), conninfo)

    assert (first.read, first.inserted) == (3, 3)
    assert (second.inserted, second.skipped) == (0, 3)
    with psycopg.connect(conninfo) as conn:
        count, empty_kwh = conn.execute(
            "SELECT count(*), count(*) FILTER (WHERE consumption_kwh IS NULL) "
            "FROM core.energy_reading WHERE site_id = %s",
            (SITE,),
        ).fetchone()
    assert (count, empty_kwh) == (3, 1)


@needs_db
def test_load_rejects_unknown_quality(conninfo):
    df = silver_rows()
    df.loc[0, "kwh_source"] = "inconnue"

    with pytest.raises(ValueError, match="inconnue"):
        load(df, conninfo)


@needs_db
def test_cli_reads_parquet(conninfo, tmp_path):
    path = tmp_path / "silver.parquet"
    silver_rows().to_parquet(path, index=False)

    assert main([str(path)]) == 0
