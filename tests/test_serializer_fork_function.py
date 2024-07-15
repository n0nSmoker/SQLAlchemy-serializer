from sqlalchemy_serializer.serializer import Serializer


def test_fork_with_key(mocker, get_serializer):
    key = "test_value"
    schema = mocker.MagicMock()
    serializer = get_serializer()

    mocker.patch.object(serializer, "schema", schema)
    result = serializer.fork(key=key)

    assert isinstance(result, Serializer)
    assert result.opts == serializer.opts
    schema.fork.assert_called_once_with(key=key)


def test_fork_logger(mocker, get_serializer):
    key = "test_key"
    mocked_logger = mocker.patch("sqlalchemy_serializer.serializer.logger")
    mocker.patch("sqlalchemy_serializer.serializer.Serializer.__call__")
    serializer = get_serializer()

    mocker.patch.object(serializer, "schema", mocker.MagicMock())
    serializer.fork(key=key)

    mocked_logger.debug.assert_called_once_with("Fork serializer for key:%s", key)
