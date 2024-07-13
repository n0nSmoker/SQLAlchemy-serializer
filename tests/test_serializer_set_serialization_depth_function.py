def test_set_serialization_depth_success(get_serializer):
    new_serialization_depth = 123
    serializer = get_serializer()

    assert serializer.serialization_depth == 0
    serializer.set_serialization_depth(new_serialization_depth)
    assert serializer.serialization_depth == new_serialization_depth
