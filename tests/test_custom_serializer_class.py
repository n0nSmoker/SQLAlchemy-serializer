import sqlalchemy as sa
from sqlalchemy_serializer import SerializerMixin, Serializer

from .models import (
    DATETIME,
    Base,
)


CUSTOM_DICT_VALUE = {'CustomModelTwo': 'test value'}


class CustomSerializer(Serializer):
    def serialize(self, value, **kwargs):
        # special case for CustomModelTwo, returning string instead of real work
        if isinstance(value, CustomModelTwo):
            return CUSTOM_DICT_VALUE
        return super().serialize(value, **kwargs)


class CustomSerializerMixin(SerializerMixin):
    serializer_class = CustomSerializer


class CustomModelOne(Base, CustomSerializerMixin):
    __tablename__ = "custom_model_one"
    id = sa.Column(sa.Integer, primary_key=True)
    datetime = sa.Column(sa.DateTime, default=DATETIME)


class CustomModelTwo(CustomModelOne):
    __tablename__ = "custom_model_two"



def test_custom_serializer(get_instance):
    """
    Very basic test to ensure custom serializer is used
    """
    # Get instance for CustomModelOne, which should serialize normally
    i = get_instance(CustomModelOne)
    data = i.to_dict()
    # Check model was processed correctly
    assert "datetime" in data
    assert data["datetime"] == DATETIME.strftime(i.datetime_format)
    # Same for CustomModelTwo, which should instead return only a simple dict
    i = get_instance(CustomModelTwo)
    data = i.to_dict()
    assert data == CUSTOM_DICT_VALUE
