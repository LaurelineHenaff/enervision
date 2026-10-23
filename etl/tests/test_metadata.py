"""Métadonnées : anomalies étiquetées et contrôle de cohérence avec les données."""
import pandas as pd

from pipeline import cleaning as ch
from pipeline import metadata as md
from pipeline.timestamps import normalize_timestamps
from tests.conftest import anomalie, metadonnees, relevés


def test_horodatages_ramenes_en_utc():
    serie = pd.Series(["2023-01-01 00:00:00", "2023-01-01T02:00:00+02:00", "2023-01-01T00:00:00Z"])
    resultat = normalize_timestamps(serie)
    assert str(resultat.dt.tz) == "UTC"
    assert resultat.nunique() == 1


def test_anomalies_etiquetees_avec_duree_et_priorite_a_la_coupure():
    meta = metadonnees(
        [
            anomalie("2023-01-01T01:00:00", "plateau", "Consommation élevée prolongée (3h)", "medium"),
            anomalie("2023-01-01T02:00:00", "outage", "Coupure électrique (1h)"),
            anomalie("2023-01-01T04:00:00", "spike", "Pic de consommation (+65%)", "high"),
        ]
    )
    df = ch.clean(relevés([1.0] * 6), meta)
    assert df["anomaly_type"].tolist()[:6] == [pd.NA, "plateau", "outage", "plateau", "spike", pd.NA]
    assert df.loc[2, "anomaly_severity"] == "critical"


def test_controle_des_metadonnees_conformes():
    df = ch.clean(relevés([1.0, 2.0, 3.0]))
    assert md.check_against_metadata(df, metadonnees()) == []


def test_controle_des_metadonnees_signale_les_ecarts():
    df = ch.clean(relevés([1.0, 2.0, 3.0]))
    meta = metadonnees(total=5, fin="2023-01-02T00:00:00")
    meta["frequency"] = "15min"
    meta["sites"]["SITE002"] = {"total_records": 1, "start_date": "2023-01-01T00:00:00", "end_date": "2023-01-01T00:00:00"}
    problemes = " | ".join(md.check_against_metadata(df, meta))
    assert "fréquence" in problemes
    assert "SITE001 : 3 lignes, 5 annoncées" in problemes
    assert "période" in problemes
    assert "SITE002 : 0 lignes, 1 annoncées" in problemes


def test_site_absent_des_metadonnees_signale():
    df = ch.clean(relevés([1.0], site="SITE009"))
    assert "SITE009 : absent des métadonnées" in md.check_against_metadata(df, metadonnees())
