from enum import Enum
import pytest


@pytest.fixture
def default_options():
    return dict(
        date_format="%Y-%m-%d",
        datetime_format="%Y-%m-%d %H:%M:%S",
        time_format="%H:%M:%S",
        decimal_format="%.2f",
        tzinfo=None,
        serialize_types=None,
        skip_none_values=None,
    )


class Numbers(Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3


class Strings(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


def test_enums(default_options, get_serializer):

    data = {
        "int_enum": Numbers.FIRST,
        "string_enum": Strings.RED,
        "list_enum": [Numbers.FIRST, Numbers.SECOND],
    }

    serializer = get_serializer(**default_options)
    result = serializer(data, only=["int_enum", "string_enum", "list_enum"])

    assert result == {
        "int_enum": Numbers.FIRST.value,
        "string_enum": Strings.RED.value,
        "list_enum": [Numbers.FIRST.value, Numbers.SECOND.value],
    }
