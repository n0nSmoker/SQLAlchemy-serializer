import uuid

from .base import Base


class UUID(Base):
    def __call__(self, value: uuid.UUID) -> str:
        return str(value)
