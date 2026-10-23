"""Classe de base déclarative dont héritent tous les modèles SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
