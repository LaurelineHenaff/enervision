"""Nettoyage de l'historique : règles (cleaning) et traitement complet (jobs.clean_history)."""
import json

import numpy as np
import pandas as pd
import pytest

from pipeline import cleaning as ch
from pipeline.jobs import clean_history as job
from tests.conftest import NAN, anomalie, metadonnees, relevés


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
