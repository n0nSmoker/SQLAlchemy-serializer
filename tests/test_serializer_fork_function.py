def test_fork_with_key(mocker, get_serializer):
    value, key, expected = "test_value", "test_key", "serialized"
    schema = mocker.MagicMock()
    serializer = get_serializer()

    mocker.patch(
        "sqlalchemy_serializer.serializer.Serializer.__call__", return_value=expected
    )

    mocker.patch.object(serializer, "schema", schema)
    result = serializer.fork(value=value, key=key)

    assert result == expected
    schema.fork.assert_called_once_with(key=key)


def test_fork_logger(mocker, get_serializer):
    value, key = "test_value", "test_key"
    mocked_logger = mocker.patch("sqlalchemy_serializer.serializer.logger")
    mocker.patch("sqlalchemy_serializer.serializer.Serializer.__call__")
    serializer = get_serializer()

    mocker.patch.object(serializer, "schema", mocker.MagicMock())
    serializer.fork(value, key=key)

    mocked_logger.debug.assert_called_once_with(
        "Fork serializer for type:%s key:%s", "str", key
    )
