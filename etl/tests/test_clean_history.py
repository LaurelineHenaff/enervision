"""Nettoyage de l'historique : règles (cleaning) et traitement complet (jobs.clean_history)."""
import json

import numpy as np
import pandas as pd
import pytest

from pipeline import cleaning as ch
from pipeline.jobs import clean_history as job

NAN = np.nan


def relevés(kwh, euros=None, site="SITE001", debut="2023-01-01 00:00:00"):
    n = len(kwh)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range(debut, periods=n, freq="h").strftime("%Y-%m-%d %H:%M:%S"),
            "site_id": site,
            "consumption_kwh": kwh,
            "consumption_euros": euros if euros is not None else [NAN] * n,
            "temperature_celsius": [10.0] * n,
        }
    )


def test_horodatages_ramenes_en_utc():
    serie = pd.Series(["2023-01-01 00:00:00", "2023-01-01T02:00:00+02:00", "2023-01-01T00:00:00Z"])
    resultat = ch.normalize_timestamps(serie)
    assert str(resultat.dt.tz) == "UTC"
    assert resultat.nunique() == 1


def test_kwh_retrouve_par_les_euros_au_tarif_mesure():
    df = ch.clean(relevés([100.0, NAN, 100.0], euros=[15.0, 30.0, 15.0]))
    assert df.loc[1, "consumption_kwh_clean"] == pytest.approx(200.0)  # 30 / 0,15
    assert df.loc[1, "consumption_kwh_source"] == ch.SOURCE_RECOVERED


def test_valeur_brute_jamais_ecrasee():
    df = ch.clean(relevés([100.0, NAN, 120.0]))
    assert np.isnan(df.loc[1, "consumption_kwh"])
    assert df.loc[1, "consumption_kwh_clean"] == pytest.approx(110.0)
    assert df.loc[1, "consumption_kwh_source"] == ch.SOURCE_INTERPOLATED


def test_les_zeros_sont_des_coupures_conservees():
    df = ch.clean(relevés([100.0, 0.0, 0.0, 100.0], euros=[15.0, 0.0, 0.0, 15.0]))
    assert df["consumption_kwh_clean"].tolist() == [100.0, 0.0, 0.0, 100.0]
    assert set(df["consumption_kwh_source"]) == {ch.SOURCE_MEASURED}


def test_trou_court_interpole_trou_long_laisse_vide():
    court = [10.0, NAN, NAN, NAN, NAN, 20.0]  # 4 valeurs : limite incluse
    long = [10.0, NAN, NAN, NAN, NAN, NAN, 20.0]  # 5 valeurs : au-delà
    assert ch.clean(relevés(court))["consumption_kwh_clean"].notna().all()

    df = ch.clean(relevés(long))
    assert df["consumption_kwh_clean"].iloc[1:6].isna().all()
    assert (df["consumption_kwh_source"].iloc[1:6] == ch.SOURCE_MISSING).all()


def test_jamais_de_remplissage_par_zero_ni_extrapolation():
    df = ch.clean(relevés([NAN, 10.0, 20.0, NAN]))
    assert np.isnan(df.loc[0, "consumption_kwh_clean"])
    assert np.isnan(df.loc[3, "consumption_kwh_clean"])


def test_interpolation_isolee_par_site():
    a = relevés([10.0, NAN], site="SITE001")
    b = relevés([30.0, 50.0], site="SITE002")
    df = ch.clean(pd.concat([a, b], ignore_index=True))
    site1 = df[df.site_id == "SITE001"]
    assert np.isnan(site1["consumption_kwh_clean"].iloc[1])  # pas de valeur voisine du même site


def test_doublons_supprimes_et_tri_chronologique():
    df = relevés([3.0, 1.0, 2.0])
    df = pd.concat([df.iloc[[2, 0, 1]], df.iloc[[0]]], ignore_index=True)
    resultat = ch.clean(df)
    assert len(resultat) == 3
    assert resultat["timestamp"].is_monotonic_increasing


def metadonnees(anomalies=(), total=3, debut="2023-01-01T00:00:00", fin="2023-01-01T02:00:00"):
    return {
        "frequency": "1h",
        "sites": {
            "SITE001": {
                "total_records": total,
                "start_date": debut,
                "end_date": fin,
                "anomalies": list(anomalies),
            }
        },
    }


def anomalie(timestamp, type_, description, severity="critical"):
    return {"timestamp": timestamp, "type": type_, "severity": severity, "description": description}


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


def test_pas_d_interpolation_dans_une_coupure_etiquetee():
    meta = metadonnees([anomalie("2023-01-01T01:00:00", "outage", "Coupure électrique (1h)")])
    df = ch.clean(relevés([10.0, NAN, 30.0, NAN, 50.0]), meta)
    assert np.isnan(df.loc[1, "consumption_kwh_clean"])  # dans la coupure : laissé vide
    assert df.loc[1, "consumption_kwh_source"] == ch.SOURCE_MISSING
    assert df.loc[3, "consumption_kwh_clean"] == pytest.approx(40.0)  # hors coupure : interpolé


def test_les_euros_retrouvent_une_valeur_meme_dans_une_coupure():
    meta = metadonnees([anomalie("2023-01-01T01:00:00", "outage", "Coupure électrique (1h)")])
    df = ch.clean(relevés([10.0, NAN, 30.0], euros=[1.5, 0.0, 4.5]), meta)
    assert df.loc[1, "consumption_kwh_clean"] == 0.0
    assert df.loc[1, "consumption_kwh_source"] == ch.SOURCE_RECOVERED


def test_sans_metadonnees_pas_de_colonnes_d_anomalie():
    assert "anomaly_type" not in ch.clean(relevés([1.0, 2.0]))


def test_controle_des_metadonnees_conformes():
    df = ch.clean(relevés([1.0, 2.0, 3.0]))
    assert ch.check_against_metadata(df, metadonnees()) == []


def test_controle_des_metadonnees_signale_les_ecarts():
    df = ch.clean(relevés([1.0, 2.0, 3.0]))
    meta = metadonnees(total=5, fin="2023-01-02T00:00:00")
    meta["frequency"] = "15min"
    meta["sites"]["SITE002"] = {"total_records": 1, "start_date": "2023-01-01T00:00:00", "end_date": "2023-01-01T00:00:00"}
    problemes = " | ".join(ch.check_against_metadata(df, meta))
    assert "fréquence" in problemes
    assert "SITE001 : 3 lignes, 5 annoncées" in problemes
    assert "période" in problemes
    assert "SITE002 : 0 lignes, 1 annoncées" in problemes


def test_site_absent_des_metadonnees_signale():
    df = ch.clean(relevés([1.0], site="SITE009"))
    assert "SITE009 : absent des métadonnées" in ch.check_against_metadata(df, metadonnees())


def test_cli_ecrit_un_parquet_avec_les_anomalies(tmp_path):
    entree, meta, sortie = tmp_path / "in.csv", tmp_path / "meta.json", tmp_path / "sortie" / "out.parquet"
    relevés([1.0, NAN, 3.0]).to_csv(entree, index=False)
    meta.write_text(json.dumps(metadonnees([anomalie("2023-01-01T01:00:00", "outage", "Coupure (1h)")])))

    job.main(["--input", str(entree), "--metadata", str(meta), "--output", str(sortie)])

    ecrit = pd.read_parquet(sortie)
    assert {"consumption_kwh", "consumption_kwh_clean", "consumption_kwh_source", "anomaly_type"} <= set(ecrit)
    assert len(ecrit) == 3
    assert ecrit["anomaly_type"].isna().tolist() == [True, False, True]
    assert ecrit.loc[1, "anomaly_type"] == "outage"


def test_cli_sans_fichier_de_metadonnees_echoue(tmp_path):
    entree = tmp_path / "in.csv"
    relevés([1.0]).to_csv(entree, index=False)
    with pytest.raises(FileNotFoundError):
        job.main(["--input", str(entree), "--metadata", str(tmp_path / "absent.json"), "--output", str(tmp_path / "o.parquet")])


def test_doublons_et_intervalles_irreguliers_journalises(caplog):
    df = relevés([1.0, 2.0, 3.0])
    df = pd.concat([df, df.iloc[[0]], relevés([4.0], debut="2023-01-01 05:00:00")], ignore_index=True)
    with caplog.at_level("WARNING"):
        ch.clean(df)
    assert "doublons" in caplog.text
    assert "intervalles différents" in caplog.text
