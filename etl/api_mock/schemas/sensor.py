from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Sensor(BaseModel):
    status: Literal["ok", "failing"]
    failing_until: datetime | None = None


class SiteSensors(BaseModel):
    site: str
    site_name: str
    overall: Literal["ok", "degraded", "critical"]
    sensors: dict[str, Sensor]
