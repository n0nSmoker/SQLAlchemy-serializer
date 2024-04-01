from datetime import datetime
from .base import Base


class DateTime(Base):
    def __init__(self, str_format: str = '%H:%M:%S', tzinfo=None) -> None:
        self.tzinfo = tzinfo
        self.str_format = str_format

    def __call__(self, value: datetime) -> str:
        if self.tzinfo:
            value = to_local_time(dt=value, tzinfo=self.tzinfo)

        return format_dt(
            tpl=self.str_format,
            dt=value
        )


def to_local_time(dt: datetime, tzinfo) -> datetime:
    normalized = dt.astimezone(tzinfo)
    return normalized.replace(tzinfo=None)


def format_dt(dt, tpl=None) -> str:
    if not tpl:
        return dt.isoformat()
    return dt.strftime(tpl)
