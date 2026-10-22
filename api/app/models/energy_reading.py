"""Mesures horaires des sites (core.energy_reading), stockées dans une hypertable TimescaleDB.

Alimentée par l'ETL : l'historique silver (CSV nettoyé) puis la collecte de l'API Mock.
"""
from datetime import datetime

from sqlalchemy import ARRAY, BigInteger, DateTime, Float, ForeignKey, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EnergyReading(Base):
    __tablename__ = "energy_reading"
    __table_args__ = (
        Index("ix_energy_reading_site_time", "site_id", text("time DESC")),
        {"schema": "core"},
    )

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("ref.site.site_id"), primary_key=True)

    consumption_kw: Mapped[float | None] = mapped_column(Float)
    consumption_kwh: Mapped[float | None] = mapped_column(Float)
    consumption_euros: Mapped[float | None] = mapped_column(Float)
    # Mesures électriques : seulement dans la collecte temps réel, vides pour l'historique
    voltage_v: Mapped[float | None] = mapped_column(Float)
    current_a: Mapped[float | None] = mapped_column(Float)
    power_factor: Mapped[float | None] = mapped_column(Float)

    temperature_celsius: Mapped[float | None] = mapped_column(Float)
    humidity_percent: Mapped[float | None] = mapped_column(Float)
    solar_irradiance_wm2: Mapped[float | None] = mapped_column(Float)

    null_reasons: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    data_quality: Mapped[str | None] = mapped_column(ForeignKey("ref.data_quality.code"))
    # Réponse brute d'origine (raw.api_response) : vide pour l'historique chargé depuis un fichier
    raw_id: Mapped[int | None] = mapped_column(BigInteger)
