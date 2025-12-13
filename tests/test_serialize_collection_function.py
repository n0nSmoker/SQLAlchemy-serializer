from sqlalchemy_serializer.serializer import serialize_collection

from .models import FlatModel


def test_serialize_collection__success(get_instance):
    num = 3
    iterable = [get_instance(FlatModel) for _ in range(num)]
    result = serialize_collection(iterable, only=("id",))
    assert isinstance(result, list)
    assert len(result) == num
    assert all(list(item.keys()) == ["id"] for item in result)
