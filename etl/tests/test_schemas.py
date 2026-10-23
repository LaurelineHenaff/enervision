"""Schéma Site : validation et conversion des données reçues de l'API Mock."""
import pytest
from pydantic import ValidationError

from mock_client.schemas.site import Site
from tests.conftest import SITE_EXEMPLE


def test_site_valide():
    site = Site.model_validate(SITE_EXEMPLE)
    assert site.site_id == "SITE001"
    assert site.capacity_kw == 250.0


def test_capacite_convertie_en_float():
    site = Site.model_validate({**SITE_EXEMPLE, "capacity_kw": "120"})
    assert site.capacity_kw == 120.0
    assert isinstance(site.capacity_kw, float)


def test_champs_inconnus_ignores():
    site = Site.model_validate({**SITE_EXEMPLE, "champ_en_plus": 42})
    assert "champ_en_plus" not in site.model_dump()


@pytest.mark.parametrize("champ", list(SITE_EXEMPLE))
def test_champ_obligatoire_manquant(champ):
    donnees = {k: v for k, v in SITE_EXEMPLE.items() if k != champ}
    with pytest.raises(ValidationError):
        Site.model_validate(donnees)


def test_capacite_non_numerique_refusee():
    with pytest.raises(ValidationError):
        Site.model_validate({**SITE_EXEMPLE, "capacity_kw": "beaucoup"})


def test_etat_global_des_capteurs_inconnu_refuse():
    from mock_client.schemas.sensor import SiteSensors

    with pytest.raises(ValidationError):
        SiteSensors(site_id="SITE001", site_name="Bureau", overall="inconnu", sensors={})
