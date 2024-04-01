from sqlalchemy_serializer.lib.serializable.base import Base


class Bytes(Base):
    def __call__(self, value: bytes) -> str:
        return value.decode()
