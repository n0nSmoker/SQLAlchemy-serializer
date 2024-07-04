import pytest

from sqlalchemy_serializer.lib.schema import Rule


@pytest.mark.parametrize(
    "text, keys, is_negative",
    [
        ("simple", ["simple"], False),
        ("double.rule", ["double", "rule"], False),
        ("-negative", ["negative"], True),
        ("-negative.rule", ["negative", "rule"], True),
    ],
)
def test_rule(text, keys, is_negative):
    rule = Rule(text)
    assert rule.keys == keys
    assert rule.is_negative == is_negative
    assert str(rule) == text
