import datetime
from .datetime import format_dt
from .base import Base


class Time(Base):
    def __init__(self, str_format: str = '%H:%M:%S') -> None:
        self.str_format = str_format

    def __call__(self, value: datetime.time):
        return format_dt(
            tpl=self.str_format,
            dt=value
        )
