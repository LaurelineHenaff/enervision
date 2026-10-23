"""Nettoyage sur le vrai fichier fourni : ignoré tant que `dvc pull` n'a pas été fait."""
import pandas as pd
import pytest

from pipeline import cleaning
from pipeline.jobs.clean_history import DEFAULT_INPUT

pytestmark = pytest.mark.skipif(not DEFAULT_INPUT.exists(), reason="fichier DVC absent : dvc pull")


@pytest.fixture(scope="module")
def nettoye():
    return cleaning.clean(pd.read_csv(DEFAULT_INPUT))


def test_origine_des_kwh(nettoye):
    assert nettoye["consumption_kwh_source"].value_counts().to_dict() == {
        cleaning.SOURCE_MEASURED: 119807,
        cleaning.SOURCE_INTERPOLATED: 1072,
        cleaning.SOURCE_RECOVERED: 353,
        cleaning.SOURCE_MISSING: 1415,
    }


def test_les_coupures_reelles_sont_conservees(nettoye):
    assert (nettoye["consumption_kwh_clean"] == 0).sum() == 1799


def test_horodatages_en_utc_sans_doublon(nettoye):
    assert str(nettoye["timestamp"].dt.tz) == "UTC"
    assert not nettoye.duplicated(["site_id", "timestamp"]).any()
    assert len(nettoye) == 122647
