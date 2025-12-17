import math

import pytest

from .models import FlatModel, NestedModel, RecursiveModel


@pytest.fixture
def three_level_recursive_model(get_instance):
    """Create a 3-level recursive model structure: root -> child -> grandchild"""
    root = get_instance(RecursiveModel)
    child_full = get_instance(RecursiveModel, parent_id=root.id)
    get_instance(RecursiveModel, parent_id=child_full.id)
    return root


def test_default_unlimited_depth(three_level_recursive_model):
    """Test that default behavior maintains unlimited depth (backward compatible)"""
    # Default should be unlimited (math.inf)
    data = three_level_recursive_model.to_dict()

    assert "children" in data
    assert "children" in data["children"][0]
    assert "children" in data["children"][0]["children"][0]

    assert "name" in data
    assert "name" in data["children"][0]
    assert "name" in data["children"][0]["children"][0]


def test_model_level_max_depth(three_level_recursive_model):
    """Test max_serialization_depth set on model class"""
    # Set max depth to 1 (only serialize direct children, not grandchildren)
    three_level_recursive_model.max_serialization_depth = 1
    data = three_level_recursive_model.to_dict()

    assert "children" in data
    # But grandchildren should not be serialized
    assert "children" not in data["children"][0]

    assert "name" in data
    assert "name" in data["children"][0]  # Name is still there


def test_per_call_max_depth(three_level_recursive_model):
    """Test max_serialization_depth passed to to_dict() method"""
    # Per-call max depth should override model-level setting
    three_level_recursive_model.max_serialization_depth = 2
    data = three_level_recursive_model.to_dict(max_serialization_depth=0)

    # At depth 0, no relationships should be serialized
    assert "children" not in data
    assert "name" in data


def test_depth_limit_enforcement_nested_model(get_instance):
    """Test depth limit enforcement with NestedModel"""
    nested = get_instance(NestedModel, model_id=get_instance(FlatModel).id)

    # At depth 0, nested relationships should not be serialized
    data = nested.to_dict(max_serialization_depth=0)
    assert "model" not in data

    # At depth 1, one level of nesting should work
    data = nested.to_dict(max_serialization_depth=1)
    assert "model" in data
    nested_model = data["model"]
    assert "id" in nested_model
    assert "string" in nested_model
    # FlatModel doesn't have a relationship back, so no further nesting


def test_depth_limit_with_rules(three_level_recursive_model):
    """Test that depth limit works together with existing rules"""
    # Combine depth limit with rules
    data = three_level_recursive_model.to_dict(
        max_serialization_depth=1, rules=("-children.id",)
    )

    assert "children" in data
    assert "id" not in data["children"][0]  # Rule applied
    assert "name" in data["children"][0]
    # Depth limit still enforced
    assert "children" not in data["children"][0]


def test_depth_limit_zero(get_instance):
    """Test that depth 0 prevents all relationship serialization"""
    root = get_instance(RecursiveModel)
    get_instance(RecursiveModel, parent_id=root.id)

    data = root.to_dict(max_serialization_depth=0)

    # Only top-level fields should be present
    assert "id" in data
    assert "name" in data
    assert "children" not in data


@pytest.mark.parametrize("depth", [1, 2])
def test_depth_limit_multiple_levels(three_level_recursive_model, depth):
    data = three_level_recursive_model.to_dict(max_serialization_depth=depth)

    for i in range(depth):
        assert "id" in data
        assert "name" in data
        if i < depth:
            assert "children" in data
            data = data["children"][0]


def test_depth_limit_infinity(three_level_recursive_model):
    """Test that math.inf allows unlimited depth"""
    data = three_level_recursive_model.to_dict(max_serialization_depth=math.inf)

    # Should serialize all levels
    assert "children" in data
    assert "children" in data["children"][0]
    assert "children" in data["children"][0]["children"][0]


def test_model_level_depth_override(get_instance):
    """Test that per-call parameter overrides model-level setting"""
    root = get_instance(RecursiveModel)
    get_instance(RecursiveModel, parent_id=root.id)

    # Set model-level depth to 1
    root.max_serialization_depth = 1
    # But override with per-call parameter
    data = root.to_dict(max_serialization_depth=0)

    # Per-call parameter should win
    assert "children" not in data


def test_to_dict_param_overrides_class_level_max_depth(three_level_recursive_model):
    """Test that max_serialization_depth parameter in to_dict()
    overrides class-level setting"""
    three_level_recursive_model.max_serialization_depth = 1

    # First, verify class-level setting works when no parameter is passed
    data_without_param = three_level_recursive_model.to_dict()
    assert "children" in data_without_param
    assert "children" not in data_without_param["children"][0]  # Child has children field

    # Now verify that passing parameter overrides class-level setting
    # Override with depth 2 (should allow grandchildren)
    data_with_override = three_level_recursive_model.to_dict(max_serialization_depth=2)
    assert "children" in data_with_override
    # Parameter override allows deeper nesting
    assert "children" in data_with_override["children"][0]

    # Override with depth 0 (should prevent all relationships)
    data_with_zero = three_level_recursive_model.to_dict(max_serialization_depth=0)
    assert "children" not in data_with_zero
    assert "id" in data_with_zero
    assert "name" in data_with_zero

    # Override with math.inf (should allow unlimited depth)
    data_with_inf = three_level_recursive_model.to_dict(max_serialization_depth=math.inf)
    assert "children" in data_with_inf
    assert "children" in data_with_inf["children"][0]
    assert "children" in data_with_inf["children"][0]["children"][0]
