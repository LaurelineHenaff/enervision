"""Routes de données protégées : prédictions, historique, recommandations."""
import asyncio

import pytest
from fastapi import HTTPException

from app.api.deps import require_role
from app.models.user import Role, User

ROUTES_PROTEGEES = ["/predictions", "/history", "/recommendations"]


@pytest.mark.parametrize("route", ROUTES_PROTEGEES)
def test_route_refusee_sans_jeton(client, route):
    assert client.get(route).status_code == 401


@pytest.mark.parametrize("route", ROUTES_PROTEGEES)
def test_route_accessible_avec_jeton(client, auth_headers, route):
    response = client.get(route, headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_predictions_format(client, auth_headers):
    predictions = client.get("/predictions", headers=auth_headers).json()
    assert len(predictions) == 6
    assert {"timestamp", "predicted_kw", "confidence"} <= set(predictions[0])


def test_history_un_point_par_heure(client, auth_headers):
    response = client.get("/history?days=1", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 24


@pytest.mark.parametrize("days", [0, 91, "abc"])
def test_history_parametre_days_invalide(client, auth_headers, days):
    response = client.get(f"/history?days={days}", headers=auth_headers)
    assert response.status_code == 422


def test_require_role_refuse_un_role_insuffisant():
    checker = require_role(Role.ADMIN)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(checker(User(role=Role.USER)))
    assert exc.value.status_code == 403


def test_require_role_accepte_le_bon_role():
    checker = require_role(Role.ADMIN)
    admin = User(role=Role.ADMIN)
    assert asyncio.run(checker(admin)) is admin
