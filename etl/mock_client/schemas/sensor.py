from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Sensor(BaseModel):
    status: Literal["ok", "failing"]
    failing_until: datetime | None = None


class SiteSensors(BaseModel):
    """État des cinq capteurs d'un site (consumption, electrical, temperature, humidity, network)."""

    site_id: str
    site_name: str
    overall: Literal["ok", "degraded", "critical"]
    sensors: dict[str, Sensor]
