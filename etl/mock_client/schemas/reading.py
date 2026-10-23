from typing import Literal

from pydantic import BaseModel, Field, field_validator

from mock_client.schemas.types import UtcDatetime


class Reading(BaseModel):
    """Mesure d'un site (/current ou /readings), alignée sur core.energy_reading.

    `timestamp` est l'heure du mock, en UTC. `consumption_kwh` (copie de `consumption_kw`) et
    `site_type` (déjà dans ref.site) ne sont pas conservés.
    """

    timestamp: UtcDatetime
    site_id: str
    consumption_kw: float | None = None
    voltage_v: float | None = None
    current_a: float | None = None
    power_factor: float | None = None
    temperature_celsius: float | None = None
    humidity_percent: float | None = None
    null_reasons: list[str] = Field(default_factory=list)
    data_quality: Literal["good", "partial", "degraded", "critical"]

    @field_validator("null_reasons", mode="before")
    @classmethod
    def _no_reason_means_empty(cls, value):
        return [] if value is None else value
