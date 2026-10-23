from typing import Literal

from pydantic import BaseModel

from mock_client.schemas.types import UtcDatetime


class Sensor(BaseModel):
    status: Literal["ok", "failing"]
    failing_until: UtcDatetime | None = None


class SiteSensors(BaseModel):
    """État des cinq capteurs d'un site (consumption, electrical, temperature, humidity, network)."""

    site_id: str
    site_name: str
    overall: Literal["ok", "degraded", "critical"]
    sensors: dict[str, Sensor]
