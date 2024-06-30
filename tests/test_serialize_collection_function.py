from sqlalchemy_serializer.serializer import serialize_collection
from .models import FlatModel


def test_serialize_collection__success(get_instance):
    iterable = [get_instance(FlatModel) for _ in range(3)]
    result = serialize_collection(iterable, only=("id",))
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(list(item.keys()) == ["id"] for item in result)
