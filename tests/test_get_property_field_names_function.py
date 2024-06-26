from sqlalchemy_serializer.lib.fields import get_property_field_names

from .models import FlatModel


def test_get_property_field_names__returns_result(get_instance):
    instance = get_instance(FlatModel)
    assert get_property_field_names(instance) == {
        "prop",
        "prop_with_bytes",
    }
