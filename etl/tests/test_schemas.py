"""Schéma Site : validation et conversion des données reçues de l'API Mock."""
import pytest
from pydantic import ValidationError

from mock_client.schemas.site import Site
from tests.conftest import SITE_EXAMPLE


def test_valid_site():
    site = Site.model_validate(SITE_EXAMPLE)
    assert site.site_id == "SITE001"
    assert site.capacity_kw == 250.0


def test_capacity_converted_to_float():
    site = Site.model_validate({**SITE_EXAMPLE, "capacity_kw": "120"})
    assert site.capacity_kw == 120.0
    assert isinstance(site.capacity_kw, float)


def test_unknown_fields_ignored():
    site = Site.model_validate({**SITE_EXAMPLE, "champ_en_plus": 42})
    assert "champ_en_plus" not in site.model_dump()


@pytest.mark.parametrize("field", list(SITE_EXAMPLE))
def test_missing_required_field(field):
    data = {k: v for k, v in SITE_EXAMPLE.items() if k != field}
    with pytest.raises(ValidationError):
        Site.model_validate(data)


def test_non_numeric_capacity_rejected():
    with pytest.raises(ValidationError):
        Site.model_validate({**SITE_EXAMPLE, "capacity_kw": "beaucoup"})


def test_unknown_overall_sensor_state_rejected():
    from mock_client.schemas.sensor import SiteSensors

    with pytest.raises(ValidationError):
        SiteSensors(site_id="SITE001", site_name="Bureau", overall="inconnu", sensors={})
