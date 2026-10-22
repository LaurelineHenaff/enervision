"""Environnement Alembic : applique les migrations avec le même moteur asynchrone que l'API."""
import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

import app.models  # noqa: F401  (enregistre les modèles sur Base.metadata)
from app.core.config import settings
from app.db.base import Base

target_metadata = Base.metadata

# Schémas gérés par nos migrations : l'autogénération ignore ceux de TimescaleDB
MANAGED_SCHEMAS = {None, "public", "ref", "core"}


def include_name(name, type_, parent_names) -> bool:
    if type_ == "schema":
        return name in MANAGED_SCHEMAS
    return True


def include_object(obj, name, type_, reflected, compare_to) -> bool:
    # Index créés par TimescaleDB sur les hypertables (ex. energy_reading_time_idx)
    if type_ == "index" and reflected and compare_to is None:
        return False
    return not (type_ == "table" and name == "alembic_version")


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_name=include_name,
        include_object=include_object,
        # La table de suivi d'Alembic reste dans public, à côté de users
        version_table_schema="public",
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


asyncio.run(run_migrations_online())
