"""Nettoyage sur le vrai fichier fourni : ignoré tant que `dvc pull` n'a pas été fait."""
import json

import pandas as pd
import pytest

from pipeline import cleaning, metadata
from pipeline.jobs.clean_history import DEFAULT_INPUT, DEFAULT_METADATA

pytestmark = pytest.mark.skipif(not DEFAULT_INPUT.exists(), reason="DVC file missing: run dvc pull")


@pytest.fixture(scope="module")
def dataset_metadata():
    return json.loads(DEFAULT_METADATA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def cleaned(dataset_metadata):
    return cleaning.clean(pd.read_csv(DEFAULT_INPUT), dataset_metadata)


def test_kwh_sources(cleaned):
    assert cleaned["consumption_kwh_source"].value_counts().to_dict() == {
        cleaning.SOURCE_MEASURED: 119807,
        cleaning.SOURCE_INTERPOLATED: 1046,
        cleaning.SOURCE_RECOVERED: 353,
        cleaning.SOURCE_MISSING: 1441,
    }


def test_real_outages_are_kept(cleaned):
    zeros = cleaned["consumption_kwh_clean"] == 0
    assert zeros.sum() == 1798
    assert (cleaned.loc[zeros, "anomaly_type"] == "outage").all()  # aucun zéro hors coupure étiquetée


def test_labelled_anomaly_counts(cleaned):
    assert cleaned["anomaly_type"].value_counts().to_dict() == {
        "plateau": 8315, "outage": 1932, "drop": 590, "spike": 569,
    }  # fmt: skip


def test_data_matches_metadata(cleaned, dataset_metadata):
    assert metadata.check_against_metadata(cleaned, dataset_metadata) == []


def test_timestamps_in_utc_without_duplicates(cleaned):
    assert str(cleaned["timestamp"].dt.tz) == "UTC"
    assert not cleaned.duplicated(["site_id", "timestamp"]).any()
    assert len(cleaned) == 122647
