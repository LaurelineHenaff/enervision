"""Référentiels (ref) et mesures horaires (core.energy_reading, hypertable).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-22
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Valeurs de kwh_source produites par l'ETL silver
DATA_QUALITY = [
    ("observed", "Mesure relevée par le capteur"),
    ("interpolated", "Trou court comblé par interpolation linéaire"),
    ("profile", "Trou long comblé par le profil typique du site"),
    ("recovered_from_euros", "kWh reconstruits à partir du montant en euros"),
]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    op.execute("CREATE SCHEMA IF NOT EXISTS ref")
    op.execute("CREATE SCHEMA IF NOT EXISTS core")

    op.create_table(
        "site_type",
        sa.Column("site_type", sa.Text, primary_key=True),
        sa.Column("label", sa.Text),
        schema="ref",
    )
    op.create_table(
        "site",
        sa.Column("site_id", sa.Text, primary_key=True),
        sa.Column("site_name", sa.Text, nullable=False),
        sa.Column("site_type", sa.Text, sa.ForeignKey("ref.site_type.site_type"), nullable=False),
        sa.Column("location", sa.Text),
        sa.Column("capacity_kw", sa.Numeric),
        sa.Column("status", sa.Text),
        schema="ref",
    )
    data_quality = op.create_table(
        "data_quality",
        sa.Column("code", sa.Text, primary_key=True),
        sa.Column("description", sa.Text, nullable=False),
        schema="ref",
    )
    op.bulk_insert(data_quality, [{"code": c, "description": d} for c, d in DATA_QUALITY])

    op.create_table(
        "energy_reading",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("site_id", sa.Text, sa.ForeignKey("ref.site.site_id"), nullable=False),
        sa.Column("consumption_kw", sa.Float),
        sa.Column("consumption_kwh", sa.Float),
        sa.Column("consumption_euros", sa.Float),
        sa.Column("voltage_v", sa.Float),
        sa.Column("current_a", sa.Float),
        sa.Column("power_factor", sa.Float),
        sa.Column("temperature_celsius", sa.Float),
        sa.Column("humidity_percent", sa.Float),
        sa.Column("solar_irradiance_wm2", sa.Float),
        sa.Column("null_reasons", postgresql.ARRAY(sa.Text)),
        sa.Column("data_quality", sa.Text, sa.ForeignKey("ref.data_quality.code")),
        # FK vers raw.api_response à ajouter quand la table existera
        sa.Column("raw_id", sa.BigInteger),
        sa.PrimaryKeyConstraint("time", "site_id"),
        schema="core",
    )
    # Hypertable découpée par mois. L'index (site_id, time) sert les requêtes par site.
    op.execute(
        "SELECT create_hypertable('core.energy_reading', by_range('time', INTERVAL '1 month'))"
    )
    op.create_index(
        "ix_energy_reading_site_time",
        "energy_reading",
        ["site_id", sa.text("time DESC")],
        schema="core",
    )


def downgrade() -> None:
    op.drop_table("energy_reading", schema="core")
    op.drop_table("data_quality", schema="ref")
    op.drop_table("site", schema="ref")
    op.drop_table("site_type", schema="ref")
    op.execute("DROP SCHEMA IF EXISTS core")
    op.execute("DROP SCHEMA IF EXISTS ref")
