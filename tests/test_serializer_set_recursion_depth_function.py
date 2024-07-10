def test_set_recursion_depth_success(serializer):
    new_recursion_depth = 123
    assert serializer.recursion_depth == 0
    serializer.set_recursion_depth(new_recursion_depth)
    assert serializer.recursion_depth == new_recursion_depth
