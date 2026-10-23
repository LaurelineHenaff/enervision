from datetime import datetime

from pydantic import BaseModel


class Reading(BaseModel):
    timestamp: datetime
    site_id: str
    site_type: str
    consumption_kw: float | None = None
    consumption_kwh: float | None = None
    voltage_v: float | None = None
    current_a: float | None = None
    power_factor: float | None = None
    temperature_celsius: float | None = None
    humidity_percent: float | None = None
    null_reasons: list[str] | None = None
    data_quality: str | None = None
