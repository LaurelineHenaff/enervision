"""Sites et mesures de consommation, lues dans ref.site et core.energy_reading."""
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, literal_column, select

from app.api.deps import CurrentUser, DbSession
from app.models import EnergyReading, Site
from app.schemas.site import (
    Bucket,
    ConsumptionBucket,
    QualityCount,
    ReadingRead,
    SiteRead,
)

router = APIRouter(prefix="/sites", tags=["sites"])

BUCKET_INTERVALS = {
    Bucket.HOUR: "1 hour",
    Bucket.DAY: "1 day",
    Bucket.WEEK: "1 week",
    Bucket.MONTH: "1 month",
}

Start = Query(default=None, description="Début inclus (ISO 8601). Par défaut : sans limite")
End = Query(default=None, description="Fin exclue (ISO 8601). Par défaut : sans limite")


async def get_site_or_404(db: DbSession, site_id: str) -> Site:
    site = await db.get(Site, site_id)
    if site is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Site {site_id} inconnu")
    return site


def in_period(query, start: datetime | None, end: datetime | None):
    if start is not None and end is not None and start >= end:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "start doit précéder end")
    if start is not None:
        query = query.where(EnergyReading.time >= start)
    if end is not None:
        query = query.where(EnergyReading.time < end)
    return query


@router.get("", response_model=list[SiteRead])
async def list_sites(current_user: CurrentUser, db: DbSession):
    return (await db.scalars(select(Site).order_by(Site.site_id))).all()


@router.get("/{site_id}", response_model=SiteRead)
async def get_site(site_id: str, current_user: CurrentUser, db: DbSession):
    return await get_site_or_404(db, site_id)


@router.get("/{site_id}/readings", response_model=list[ReadingRead])
async def list_readings(
    site_id: str,
    current_user: CurrentUser,
    db: DbSession,
    start: datetime | None = Start,
    end: datetime | None = End,
    limit: int = Query(default=168, ge=1, le=1000, description="168 = une semaine"),
    offset: int = Query(default=0, ge=0),
):
    """Mesures horaires, de la plus ancienne à la plus récente."""
    await get_site_or_404(db, site_id)
    query = select(EnergyReading).where(EnergyReading.site_id == site_id)
    query = in_period(query, start, end).order_by(EnergyReading.time).limit(limit).offset(offset)
    return (await db.scalars(query)).all()


@router.get("/{site_id}/consumption", response_model=list[ConsumptionBucket])
async def get_consumption(
    site_id: str,
    current_user: CurrentUser,
    db: DbSession,
    bucket: Bucket = Bucket.DAY,
    start: datetime | None = Start,
    end: datetime | None = End,
):
    """Consommation agrégée par période, calculée par time_bucket de TimescaleDB."""
    await get_site_or_404(db, site_id)
    period = func.time_bucket(
        literal_column(f"INTERVAL '{BUCKET_INTERVALS[bucket]}'"), EnergyReading.time
    ).label("start")
    query = (
        select(
            period,
            func.sum(EnergyReading.consumption_kwh).label("consumption_kwh"),
            func.sum(EnergyReading.consumption_euros).label("consumption_euros"),
            func.avg(EnergyReading.consumption_kw).label("avg_consumption_kw"),
            func.max(EnergyReading.consumption_kw).label("max_consumption_kw"),
            func.avg(EnergyReading.temperature_celsius).label("avg_temperature_celsius"),
            func.count().label("nb_readings"),
        )
        .where(EnergyReading.site_id == site_id)
        .group_by(period)
        .order_by(period)
    )
    rows = (await db.execute(in_period(query, start, end))).mappings().all()
    return [ConsumptionBucket(**row) for row in rows]


@router.get("/{site_id}/quality", response_model=list[QualityCount])
async def get_quality(
    site_id: str,
    current_user: CurrentUser,
    db: DbSession,
    start: datetime | None = Start,
    end: datetime | None = End,
):
    """Répartition des mesures par origine : observées, interpolées, reconstruites..."""
    await get_site_or_404(db, site_id)
    query = (
        select(EnergyReading.data_quality, func.count().label("nb_readings"))
        .where(EnergyReading.site_id == site_id)
        .group_by(EnergyReading.data_quality)
        .order_by(func.count().desc())
    )
    rows = (await db.execute(in_period(query, start, end))).all()
    total = sum(n for _, n in rows)
    return [
        QualityCount(data_quality=quality, nb_readings=n, share=round(n / total, 4))
        for quality, n in rows
    ]
