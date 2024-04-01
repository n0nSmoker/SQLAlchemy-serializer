import enum
from sqlalchemy_serializer.lib.serializable.base import Base


class Enum(Base):
    def __call__(self, value: enum.Enum) -> str:
        return value.value