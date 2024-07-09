import pytest

from sqlalchemy_serializer.serializer import Serializer


@pytest.fixture
def test_class():
    serializer = Serializer(
        date_format="%Y-%m-%d",
        datetime_format="%Y-%m-%d %H:%M:%S",
        time_format="%H:%M",
        decimal_format="{}",
        tzinfo=None,
        serialize_types=(),
    )
    return serializer


def test_set_recursion_depth_success(test_class):
    new_recursion_depth = 123
    assert test_class.recursion_depth == 0
    test_class.set_recursion_depth(new_recursion_depth)
    assert test_class.recursion_depth == new_recursion_depth
