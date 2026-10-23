"""Métadonnées : anomalies étiquetées et contrôle de cohérence avec les données."""
import pandas as pd

from pipeline import cleaning as ch
from pipeline import metadata as md
from pipeline.timestamps import normalize_timestamps
from tests.conftest import make_anomaly, make_metadata, make_readings


def test_timestamps_normalized_to_utc():
    series = pd.Series(["2023-01-01 00:00:00", "2023-01-01T02:00:00+02:00", "2023-01-01T00:00:00Z"])
    result = normalize_timestamps(series)
    assert str(result.dt.tz) == "UTC"
    assert result.nunique() == 1


def test_labelled_anomalies_with_duration_and_outage_priority():
    meta = make_metadata(
        [
            make_anomaly("2023-01-01T01:00:00", "plateau", "Consommation élevée prolongée (3h)", "medium"),
            make_anomaly("2023-01-01T02:00:00", "outage", "Coupure électrique (1h)"),
            make_anomaly("2023-01-01T04:00:00", "spike", "Pic de consommation (+65%)", "high"),
        ]
    )
    df = ch.clean(make_readings([1.0] * 6), meta)
    assert df["anomaly_type"].tolist()[:6] == [pd.NA, "plateau", "outage", "plateau", "spike", pd.NA]
    assert df.loc[2, "anomaly_severity"] == "critical"


def test_metadata_check_passes():
    df = ch.clean(make_readings([1.0, 2.0, 3.0]))
    assert md.check_against_metadata(df, make_metadata()) == []


def test_metadata_check_reports_differences():
    df = ch.clean(make_readings([1.0, 2.0, 3.0]))
    meta = make_metadata(total=5, end="2023-01-02T00:00:00")
    meta["frequency"] = "15min"
    meta["sites"]["SITE002"] = {"total_records": 1, "start_date": "2023-01-01T00:00:00", "end_date": "2023-01-01T00:00:00"}
    problems_text = " | ".join(md.check_against_metadata(df, meta))
    assert "frequency" in problems_text
    assert "SITE001: 3 rows, 5 announced" in problems_text
    assert "period" in problems_text
    assert "SITE002: 0 rows, 1 announced" in problems_text


def test_site_missing_from_metadata_reported():
    df = ch.clean(make_readings([1.0], site="SITE009"))
    assert "SITE009: absent from the metadata" in md.check_against_metadata(df, make_metadata())
