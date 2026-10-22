"""Référentiels (schéma ref) : types de site, sites, qualité des mesures."""
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SiteType(Base):
    __tablename__ = "site_type"
    __table_args__ = ({"schema": "ref"},)

    site_type: Mapped[str] = mapped_column(Text, primary_key=True)
    label: Mapped[str | None] = mapped_column(Text)


class Site(Base):
    __tablename__ = "site"
    __table_args__ = ({"schema": "ref"},)

    site_id: Mapped[str] = mapped_column(Text, primary_key=True)
    site_name: Mapped[str] = mapped_column(Text)
    site_type: Mapped[str] = mapped_column(ForeignKey("ref.site_type.site_type"))
    location: Mapped[str | None] = mapped_column(Text)
    capacity_kw: Mapped[Decimal | None] = mapped_column(Numeric)
    status: Mapped[str | None] = mapped_column(Text)


class DataQuality(Base):
    """Origine d'une mesure de consommation : observée, interpolée, reconstruite..."""

    __tablename__ = "data_quality"
    __table_args__ = ({"schema": "ref"},)

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    description: Mapped[str] = mapped_column(Text)
