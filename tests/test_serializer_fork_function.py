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


def test_fork_with_none_key(mocker, test_class):
    value = "test_value"
    expected = "serialized"
    schema = mocker.MagicMock()
    mocker.patch(
        "sqlalchemy_serializer.serializer.Serializer.__call__", return_value=expected
    )

    with mocker.patch.object(test_class, "schema", schema):
        result = test_class.fork(value)

    assert result == expected
    schema.fork.assert_not_called()


def test_fork_with_key(mocker, test_class):
    value, key, expected = "test_value", "test_key", "serialized"
    schema = mocker.MagicMock()

    mocker.patch(
        "sqlalchemy_serializer.serializer.Serializer.__call__", return_value=expected
    )

    with mocker.patch.object(test_class, "schema", schema):
        result = test_class.fork(value=value, key=key)

    assert result == expected
    schema.fork.assert_called_once_with(key=key)


def test_fork_logger(mocker, test_class):
    mocked_logger = mocker.patch("sqlalchemy_serializer.serializer.logger")
    mocker.patch("sqlalchemy_serializer.serializer.Serializer.__call__")

    with mocker.patch.object(test_class, "schema", mocker.MagicMock()):
        test_class.fork("value")

    mocked_logger.debug.assert_called_once_with(
        "Fork serializer for type:%s", "str"
    )
