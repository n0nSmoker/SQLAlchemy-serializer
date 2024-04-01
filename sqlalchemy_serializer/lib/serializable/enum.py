import enum
from .base import Base


class Enum(Base):
    def __call__(self, value: enum.Enum) -> str:
        return value.value
