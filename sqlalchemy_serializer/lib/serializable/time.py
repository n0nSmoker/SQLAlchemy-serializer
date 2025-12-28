import datetime

from .base import Base
from .datetime import format_dt


class Time(Base):
    def __init__(self, str_format: str = "%H:%M:%S") -> None:
        self.str_format = str_format

    def __call__(self, value: datetime.time) -> str:
        return format_dt(tpl=self.str_format, dt=value)
