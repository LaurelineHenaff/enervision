from datetime import datetime

from pydantic import BaseModel


class Alert(BaseModel):
    alert_id: str
    timestamp: datetime
    site_id: str
    severity: str
    type: str
    message: str
    value: float | None = None
    threshold: float
