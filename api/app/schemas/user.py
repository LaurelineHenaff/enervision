"""Schémas Pydantic : ce qui entre et sort de l'API pour les utilisateurs.

Séparer les schémas des modèles SQL évite d'exposer le hash du mot de passe :
UserRead ne contient jamais hashed_password.
UserCreate ne contient jamais role : impossible de s'inscrire en admin.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    role: Role
    created_at: datetime
