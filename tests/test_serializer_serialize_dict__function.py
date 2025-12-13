from decimal import Decimal

import pytest


@pytest.fixture
def test_dict():
    return {
        "int": 123,
        "float": 12.3,
        "decimal": Decimal("12.3"),
        "str": "!@#$%^",
        "callable": lambda: {"str": "value", "int": 1234},
        "list_of_dicts": [
            {
                "str": "string",
                "int": 1235,
            }
        ],
    }


def test_serializer_serialize_dict__success(get_serializer, test_dict):
    serializer = get_serializer()
    result = serializer.serialize_dict(test_dict)
    assert result == {
        "int": 123,
        "float": 12.3,
        "decimal": "12.3",
        "str": "!@#$%^",
        "callable": {"str": "value", "int": 1234},
        "list_of_dicts": [
            {
                "str": "string",
                "int": 1235,
            }
        ],
    }


@pytest.mark.parametrize(
    "only, expected",
    [
        (("int",), {"int": 123}),
        (("callable.int",), {"callable": {"int": 1234}}),
        (("list_of_dicts.int",), {"list_of_dicts": [{"int": 1235}]}),
    ],
)
def test_serializer_serialize_dict__fork_success(get_serializer, test_dict, only, expected):
    serializer = get_serializer()
    serializer.schema.update(only=only)
    result = serializer.serialize_dict(test_dict)
    assert result == expected
