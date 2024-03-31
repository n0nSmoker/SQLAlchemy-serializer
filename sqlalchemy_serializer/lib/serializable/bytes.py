from .base import Base


class Bytes(Base):
    def __call__(self, value: bytes) -> str:
        return value.decode()
