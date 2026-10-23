"""Nettoyage sur le vrai fichier fourni : ignoré tant que `dvc pull` n'a pas été fait."""
import json

import pandas as pd
import pytest

from pipeline import cleaning, metadata
from pipeline.jobs.clean_history import DEFAULT_INPUT, DEFAULT_METADATA

pytestmark = pytest.mark.skipif(not DEFAULT_INPUT.exists(), reason="fichier DVC absent : dvc pull")


@pytest.fixture(scope="module")
def metadonnees():
    return json.loads(DEFAULT_METADATA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def nettoye(metadonnees):
    return cleaning.clean(pd.read_csv(DEFAULT_INPUT), metadonnees)


def test_origine_des_kwh(nettoye):
    assert nettoye["consumption_kwh_source"].value_counts().to_dict() == {
        cleaning.SOURCE_MEASURED: 119807,
        cleaning.SOURCE_INTERPOLATED: 1046,
        cleaning.SOURCE_RECOVERED: 353,
        cleaning.SOURCE_MISSING: 1441,
    }


def test_les_coupures_reelles_sont_conservees(nettoye):
    zeros = nettoye["consumption_kwh_clean"] == 0
    assert zeros.sum() == 1798
    assert (nettoye.loc[zeros, "anomaly_type"] == "outage").all()  # aucun zéro hors coupure étiquetée


def test_anomalies_etiquetees(nettoye):
    assert nettoye["anomaly_type"].value_counts().to_dict() == {
        "plateau": 8315, "outage": 1932, "drop": 590, "spike": 569,
    }  # fmt: skip


def test_donnees_conformes_aux_metadonnees(nettoye, metadonnees):
    assert metadata.check_against_metadata(nettoye, metadonnees) == []


def test_horodatages_en_utc_sans_doublon(nettoye):
    assert str(nettoye["timestamp"].dt.tz) == "UTC"
    assert not nettoye.duplicated(["site_id", "timestamp"]).any()
    assert len(nettoye) == 122647
