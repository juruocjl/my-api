from datetime import UTC, date, datetime, time
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.core.config import settings


@lru_cache(maxsize=1)
def get_business_timezone() -> ZoneInfo:
    return ZoneInfo(settings.business_timezone)


def utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def business_now() -> datetime:
    return datetime.now(get_business_timezone())


def business_today() -> date:
    return business_now().date()


def utc_naive_to_business(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(get_business_timezone())


def local_date_range_to_utc_naive(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    tz = get_business_timezone()
    start_local = datetime.combine(start_date, time.min, tzinfo=tz)
    end_local = datetime.combine(end_date, time.max, tzinfo=tz)
    return (
        start_local.astimezone(UTC).replace(tzinfo=None),
        end_local.astimezone(UTC).replace(tzinfo=None),
    )


def local_datetime_to_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=get_business_timezone())
    return dt.astimezone(UTC).replace(tzinfo=None)