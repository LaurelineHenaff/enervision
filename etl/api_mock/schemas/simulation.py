from pydantic import BaseModel, Field


class Simulation(BaseModel):
    duration_minutes: int = Field(
        default=30, ge=1, le=240, description="Durée du pic simulé en minutes (1 à 240)"
    )
