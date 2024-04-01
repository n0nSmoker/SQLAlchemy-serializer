import datetime
from .datetime import format_dt
from .base import Base


class Date(Base):
    def __init__(self, str_format: str = '%Y-%m-%d') -> None:
        self.str_format = str_format

    def __call__(self, value: datetime.date) -> str:
        return format_dt(
            tpl=self.str_format,
            dt=value
        )