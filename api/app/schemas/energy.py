"""Schémas Pydantic pour les données énergétiques exposées au front."""
from datetime import datetime

from pydantic import BaseModel


class PeakPrediction(BaseModel):
    timestamp: datetime
    predicted_kw: float
    confidence: float


class ConsumptionPoint(BaseModel):
    timestamp: datetime
    consumption_kw: float


class Recommendation(BaseModel):
    id: int
    title: str
    message: str
    estimated_saving_kw: float
