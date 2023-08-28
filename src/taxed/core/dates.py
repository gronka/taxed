from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from typing import Tuple


def timestamps_from_ym(year: int, month: int) -> Tuple[int, int]:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = datetime(year, month, 1, tzinfo=timezone.utc) \
        + relativedelta(months=+1)

    start_ms = start.timestamp()
    end_ms = end.timestamp()
    return (int(start_ms), int(end_ms))

def now():
    return datetime.now(timezone.utc)

def nowstamp():
    return now().timestamp() * 1000

def in_x_days(days: int) -> datetime:
    return now() + relativedelta(days=+days)

def in_x_hours(hours: int) -> datetime:
    return now() + relativedelta(hours=+hours)

def in_x_minutes(minutes: int) -> datetime:
    return now() + relativedelta(minutes=+minutes)

def in_x_months(months: int) -> datetime:
    return now() + relativedelta(months=+months)


def date_from_period(period: int) -> datetime:
    year = period // 100
    month = abs(period) % 100
    return datetime(year, month, 1, tzinfo=timezone.utc)

def period_from_ym(year: int, month: int) -> int:
    return year * 100 + month

def period_from_date(date: datetime) -> int:
    return date.year * 100 + date.month

def timestamps_from_period(period: int) -> Tuple[int, int]:
    date = date_from_period(period)
    return timestamps_from_ym(date.year, date.month)

def get_period_now() -> int:
    now = datetime.now(timezone.utc)
    return period_from_date(now)

def make_previous_period(period: int) -> int:
    year = period // 100
    month = abs(period) % 100
    date = datetime(year, month, 1, tzinfo=timezone.utc) \
        + relativedelta(months=-1)
    return period_from_date(date)

def make_next_period(period: int) -> int:
    year = period // 100
    month = abs(period) % 100
    date = datetime(year, month, 1, tzinfo=timezone.utc) \
        + relativedelta(months=+1)
    return period_from_date(date)
