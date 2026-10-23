from pydantic import BaseModel


class Statistic(BaseModel):
    site_id: str
    site_name: str
    current_consumption_kw: float
    capacity_kw: int
    load_percent: float
    data_quality: str
