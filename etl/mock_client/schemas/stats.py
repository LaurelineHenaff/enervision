from datetime import datetime

from pydantic import BaseModel


class SiteStat(BaseModel):
    site_id: str
    site_name: str
    # Nulle quand le capteur de consommation du site est en panne
    current_consumption_kw: float | None
    capacity_kw: float
    load_percent: float | None = None
    data_quality: str


class StatsSummary(BaseModel):
    """Synthèse instantanée du parc (/stats/summary).

    Les sites à consommation nulle sont exclus de total_consumption_kw : à signaler comme
    donnée incomplète.
    """

    timestamp: datetime
    total_sites: int
    total_consumption_kw: float
    total_capacity_kw: float
    average_load_percent: float
    sites: list[SiteStat]
