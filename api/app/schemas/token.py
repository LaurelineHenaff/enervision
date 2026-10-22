"""Schémas Pydantic pour les jetons JWT renvoyés à la connexion."""
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
