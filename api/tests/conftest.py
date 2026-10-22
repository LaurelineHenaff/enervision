"""Fixtures des tests de l'API.

Les tests tournent sur une vraie base TimescaleDB migrée (alembic upgrade head),
désignée par DATABASE_URL : le conteneur db en local, un service de la CI sinon.
"""
import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

if not os.environ.get("DATABASE_URL"):
    raise pytest.UsageError(
        "DATABASE_URL absente : la définir vers la base locale, voir api/README.md (Tests)"
    )
os.environ.setdefault("SECRET_KEY", "cle-de-test")

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.main import app

SITE = "TEST_API"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_client(client):
    """Client connecté avec un compte créé pour le test."""
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    password = "motdepasse-test"
    assert (await client.post("/auth/register", json={"email": email, "password": password})).status_code == 201
    token = (await client.post("/auth/login", data={"username": email, "password": password})).json()
    client.headers["Authorization"] = f"Bearer {token['access_token']}"
    yield client
    async with AsyncSessionLocal() as db:
        await db.execute(text("DELETE FROM users WHERE email = :e"), {"e": email})
        await db.commit()


@pytest.fixture
async def site_with_readings():
    """Un site de test avec 48 heures de mesures (2 jours) : 1 kWh puis 2 kWh par heure."""
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("INSERT INTO ref.site_type (site_type) VALUES ('office') ON CONFLICT DO NOTHING")
        )
        await db.execute(
            text(
                "INSERT INTO ref.site (site_id, site_name, site_type) "
                "VALUES (:s, 'Site de test', 'office') ON CONFLICT DO NOTHING"
            ),
            {"s": SITE},
        )
        await db.execute(
            text(
                """
                INSERT INTO core.energy_reading
                    (time, site_id, consumption_kw, consumption_kwh, consumption_euros,
                     temperature_celsius, data_quality)
                SELECT t, :s, k, k, k * 0.15, 10, CASE WHEN h = 0 THEN 'interpolated' ELSE 'observed' END
                FROM generate_series(0, 47) AS h,
                     LATERAL (SELECT TIMESTAMPTZ '2023-01-01 00:00+00' + h * INTERVAL '1 hour' AS t,
                                     CASE WHEN h < 24 THEN 1.0 ELSE 2.0 END AS k) AS v
                """
            ),
            {"s": SITE},
        )
        await db.commit()
    yield SITE
    async with AsyncSessionLocal() as db:
        await db.execute(text("DELETE FROM core.energy_reading WHERE site_id = :s"), {"s": SITE})
        await db.execute(text("DELETE FROM ref.site WHERE site_id = :s"), {"s": SITE})
        await db.commit()
