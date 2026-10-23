from pydantic import BaseModel


class SiteInfo(BaseModel):
    site_id: str
    site_type: str
    site_name: str
    location: str
    capacity_kw: float
    status: str
