"""Schémas Pydantic des sites et de leurs mesures."""
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class SiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    site_id: str
    site_name: str
    site_type: str
    location: str | None
    capacity_kw: Decimal | None
    status: str | None


class ReadingRead(BaseModel):
    """Une mesure horaire de core.energy_reading."""

    model_config = ConfigDict(from_attributes=True)

    time: datetime
    consumption_kw: float | None
    consumption_kwh: float | None
    consumption_euros: float | None
    voltage_v: float | None
    current_a: float | None
    power_factor: float | None
    temperature_celsius: float | None
    humidity_percent: float | None
    solar_irradiance_wm2: float | None
    null_reasons: list[str] | None
    data_quality: str | None


class Bucket(StrEnum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class ConsumptionBucket(BaseModel):
    """Consommation agrégée sur une période (heure, jour, semaine ou mois)."""

    start: datetime
    consumption_kwh: float | None
    consumption_euros: float | None
    avg_consumption_kw: float | None
    max_consumption_kw: float | None
    avg_temperature_celsius: float | None
    nb_readings: int


class QualityCount(BaseModel):
    """Nombre de mesures par origine (observée, interpolée...)."""

    data_quality: str | None
    nb_readings: int
    share: float
