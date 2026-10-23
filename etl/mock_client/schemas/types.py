from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator


def _to_utc(moment: datetime) -> datetime:
    # /current renvoie des horodatages sans fuseau, /readings en UTC ("Z") : sans fuseau = UTC
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


UtcDatetime = Annotated[datetime, AfterValidator(_to_utc)]
