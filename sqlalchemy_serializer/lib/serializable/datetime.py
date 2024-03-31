from datetime import datetime
from sqlalchemy_serializer.lib.timezones import format_dt, to_local_time
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