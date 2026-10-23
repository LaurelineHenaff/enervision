from pydantic import BaseModel

from mock_client.schemas.types import UtcDatetime


class Alert(BaseModel):
    alert_id: str
    timestamp: UtcDatetime
    site_id: str
    severity: str
    type: str
    message: str
    value: float | None = None
    threshold: float
