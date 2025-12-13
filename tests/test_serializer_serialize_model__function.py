import pytest

from tests.models import FlatModel, NestedModel


@pytest.fixture
def test_model(get_instance):
    model = get_instance(NestedModel)
    model.model = get_instance(FlatModel)
    return model


# TODO: Add more checks of model fields
@pytest.mark.parametrize(
    "only, expected",
    [
        # FIXME: last `key` ignored and all the rist is returned is it expected?
        # (("model.list.key",), {"model": {"list": [{"key": 123}]}}),
        (("dict.key",), {"dict": {"key": 123}}),
        (("bool",), {"bool": False}),
        (("null",), {"null": None}),  # FIXME: Invalid JSON
    ],
)
def test_serializer_serialize_model__fork_success(get_serializer, test_model, only, expected):
    serializer = get_serializer()
    serializer.schema.update(only=only)
    result = serializer.serialize_model(test_model)
    assert result == expected
