from .models import FlatModel, NestedModel


def test_serialize_columns_class_level(get_instance):
    """Test class-level serialize_columns attribute"""

    class CustomFlatModel(FlatModel):
        serialize_columns = {
            "id": lambda v: str(v),
            "string": lambda v: v.upper() if v else None,
        }

    i = get_instance(CustomFlatModel)
    data = i.to_dict()

    # Custom serializer should be applied
    assert "id" in data
    assert isinstance(data["id"], str)
    assert data["id"] == str(i.id)

    assert "string" in data
    assert data["string"] == i.string.upper()

    # Other fields should use normal serialization
    assert "bool" in data
    assert data["bool"] == i.bool


def test_serialize_columns_parameter_level(get_instance):
    """Test parameter-level serialize_columns in to_dict()"""
    i = get_instance(FlatModel)
    data = i.to_dict(
        serialize_columns={
            "id": lambda v: f"ID_{v}",
            "string": lambda v: v.lower() if v else None,
        }
    )

    # Custom serializer should be applied
    assert "id" in data
    assert data["id"] == f"ID_{i.id}"

    assert "string" in data
    assert data["string"] == i.string.lower()

    # Other fields should use normal serialization
    assert "bool" in data
    assert data["bool"] == i.bool


def test_serialize_columns_replaces_normal_serialization(get_instance):
    """Test that custom serializer replaces normal serialization"""
    i = get_instance(FlatModel)

    # Custom serializer that returns a fixed value
    data = i.to_dict(
        serialize_columns={
            "id": lambda _: "CUSTOM_ID",
            "bool": lambda _: "CUSTOM_BOOL",
        }
    )

    # Custom serializers should be used instead of normal serialization
    assert data["id"] == "CUSTOM_ID"
    assert data["bool"] == "CUSTOM_BOOL"

    # Other fields should still use normal serialization
    assert data["string"] == i.string


def test_serialize_columns_with_none_value(get_instance):
    """Test custom serializer with None values"""
    i = get_instance(FlatModel)
    i.null = None

    data = i.to_dict(
        serialize_columns={
            "null": lambda v: "NULL_VALUE" if v is None else v,
        }
    )

    assert "null" in data
    assert data["null"] == "NULL_VALUE"


def test_serialize_columns_with_callable_value(get_instance):
    """Test custom serializer with callable values"""
    i = get_instance(FlatModel)

    # The serializer should receive the result of the callable, not the callable itself
    data = i.to_dict(
        serialize_columns={
            "method": lambda v: f"METHOD_RESULT: {v}",
        },
        rules=("method",),
    )

    assert "method" in data
    assert "METHOD_RESULT:" in data["method"]
    assert i.method() in data["method"]


def test_serialize_columns_backward_compatibility(get_instance):
    """Test that empty dict default doesn't break anything"""
    i = get_instance(FlatModel)

    # Should work exactly as before when serialize_columns is not provided
    data = i.to_dict()

    assert "id" in data
    assert data["id"] == i.id
    assert "string" in data
    assert data["string"] == i.string
    assert "bool" in data
    assert data["bool"] == i.bool


def test_serialize_columns_parameter_overrides_class(get_instance):
    """Test that parameter-level serialize_columns overrides class-level"""

    class CustomFlatModel(FlatModel):
        serialize_columns = {
            "id": lambda v: f"CLASS_{v}",
        }

    i = get_instance(CustomFlatModel)

    # Parameter should override class-level
    data = i.to_dict(
        serialize_columns={
            "id": lambda v: f"PARAM_{v}",
        }
    )

    assert "id" in data
    assert data["id"] == f"PARAM_{i.id}"
    assert "CLASS_" not in data["id"]


def test_serialize_columns_with_nested_model(get_instance):
    """Test custom serializer with nested models/relationships"""
    flat = get_instance(FlatModel)
    nested = get_instance(NestedModel, model_id=flat.id)
    nested.model = flat

    data = nested.to_dict(
        rules=("model",),
        serialize_columns={
            "model": lambda v: {"custom": "serialized", "id": v.id} if v else None,
        },
    )

    assert "model" in data
    assert data["model"]["custom"] == "serialized"
    assert data["model"]["id"] == flat.id
    # Normal serialization should be bypassed
    assert "string" not in data["model"]


def test_serialize_columns_with_dict(get_instance):
    """Test custom serializer with nested dictionaries"""
    i = get_instance(FlatModel)
    i.dict = {"key": 123, "key2": 456}

    data = i.to_dict(
        rules=("dict",),
        serialize_columns={
            "dict": lambda v: {"custom": "dict", "original": v},
        },
    )

    assert "dict" in data
    assert data["dict"]["custom"] == "dict"
    assert data["dict"]["original"] == {"key": 123, "key2": 456}


def test_serialize_columns_passed_through_fork(get_instance):
    """Test that custom serializer is passed through forks correctly"""
    flat = get_instance(FlatModel)
    nested = get_instance(NestedModel, model_id=flat.id)
    nested.model = flat

    # Custom serializer for nested field
    data = nested.to_dict(
        rules=("model", "model.id"),
        serialize_columns={
            "id": lambda v: f"ID_{v}",  # Should apply to nested model's id
        },
    )

    assert "model" in data
    assert "id" in data["model"]
    # The custom serializer should be applied to the nested model's id
    assert data["model"]["id"] == f"ID_{flat.id}"


def test_serialize_columns_only_applies_to_matching_keys(get_instance):
    """Test that custom serializers only apply to matching column names"""
    i = get_instance(FlatModel)

    data = i.to_dict(
        serialize_columns={
            "id": lambda _: "CUSTOM",
            "nonexistent": lambda _: "SHOULD_NOT_APPEAR",
        }
    )

    # Only matching keys should use custom serializer
    assert data["id"] == "CUSTOM"
    assert "nonexistent" not in data

    # Other fields should use normal serialization
    assert data["string"] == i.string
    assert data["bool"] == i.bool


def test_serialize_columns_with_multiple_fields(get_instance):
    """Test custom serializers with multiple fields"""
    i = get_instance(FlatModel)

    data = i.to_dict(
        serialize_columns={
            "id": lambda v: str(v),
            "string": lambda v: v.upper() if v else None,
            "bool": lambda v: "YES" if v else "NO",
        }
    )

    assert isinstance(data["id"], str)
    assert data["string"] == i.string.upper()
    assert data["bool"] == "YES"  # i.bool is True by default


def test_serialize_columns_class_level_with_nested(get_instance):
    """Test class-level serialize_columns with nested structures"""

    class CustomNestedModel(NestedModel):
        serialize_columns = {
            "id": lambda v: f"NESTED_ID_{v}",
        }

    flat = get_instance(FlatModel)
    nested = get_instance(CustomNestedModel, model_id=flat.id)
    nested.model = flat

    data = nested.to_dict(rules=("id", "model", "model.id"))

    # Class-level custom serializer should apply
    assert data["id"] == f"NESTED_ID_{nested.id}"
    assert data["model"]["id"] == f"NESTED_ID_{flat.id}"
