from sqlalchemy_serializer.lib.fields import get_serializable_keys
from tests.models import FlatModel


def test_get_serializable_keys__custom_only(get_instance):
    instance = get_instance(FlatModel)
    instance.serializable_keys = ("id", "string")
    assert get_serializable_keys(instance) == {"id", "string"}


def test_get_serializable_keys__sql_only(get_instance):
    instance = get_instance(FlatModel)
    assert not instance.serializable_keys
    assert not instance.auto_serialize_properties
    assert get_serializable_keys(instance) == {
        "id",
        "string",
        "date",
        "datetime",
        "time",
        "bool",
        "null",
        "uuid",
    }


def test_get_serializable_keys__auto_serialize_propereties(get_instance):
    instance = get_instance(FlatModel)
    instance.auto_serialize_properties = True
    assert not instance.serializable_keys
    assert get_serializable_keys(instance) == {
        "id",
        "string",
        "date",
        "datetime",
        "time",
        "bool",
        "null",
        "uuid",
        "prop",
        "prop_with_bytes",
    }
