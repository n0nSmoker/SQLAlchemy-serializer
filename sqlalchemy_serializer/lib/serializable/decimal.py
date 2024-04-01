import decimal
from .base import Base


class Decimal(Base):
    def __init__(self, str_format: str = '%H:%M:%S') -> None:
        self.str_format = str_format

    def __call__(self, value: decimal.Decimal) -> str:
        return self.str_format.format(value)
