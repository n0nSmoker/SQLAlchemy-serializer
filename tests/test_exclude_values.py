from .models import FlatModel, NestedModel


def test_exclude_values_none(get_instance):
    """Test excluding None values from serialized output"""
    i = get_instance(FlatModel)
    data = i.to_dict(exclude_values=(None,))

    # None value should be excluded
    assert "null" not in data
    # Other fields should still be present
    assert "id" in data
    assert "string" in data
    assert "bool" in data


def test_exclude_values_multiple(get_instance):
    """Test excluding multiple values from serialized output"""
    i = get_instance(FlatModel)
    data = i.to_dict(exclude_values=(None, True, i.string))

    assert "null" not in data
    assert "bool" not in data
    assert "string" not in data

    # Other fields should still be present
    assert "id" in data
    assert "date" in data
    assert "datetime" in data
    assert "time" in data
    assert "uuid" in data


def test_exclude_values_with_rules(get_instance):
    """Test that exclude_values works with rules parameter"""
    i = get_instance(FlatModel)
    data = i.to_dict(rules=("null", "prop"), exclude_values=(None,))

    # null field should be included in rules but excluded by exclude_values
    assert "null" not in data
    # prop should be present
    assert "prop" in data


def test_exclude_values_with_only(get_instance):
    """Test that exclude_values works with only parameter"""
    i = get_instance(FlatModel)
    data = i.to_dict(only=("id", "null", "string"), exclude_values=(None,))

    # null field should be included in only but excluded by exclude_values
    assert "null" not in data
    # Other fields should be present
    assert "id" in data
    assert "string" in data


def test_exclude_values_empty_collection(get_instance):
    """Test that empty exclude_values doesn't filter anything"""
    i = get_instance(FlatModel)
    data = i.to_dict(exclude_values=())

    # All fields should be present including null
    assert "null" in data
    assert data["null"] is None
    assert "id" in data
    assert "string" in data


def test_exclude_values_nested_dict(get_instance):
    """Test that exclude_values works with nested dictionaries"""
    i = get_instance(FlatModel)
    # Create a dict with None value
    i.dict = {"key": 123, "null_key": None, "key2": 456}
    data = i.to_dict(rules=("dict",), exclude_values=(None,))

    assert "dict" in data
    assert "null_key" not in data["dict"]
    assert "key" in data["dict"]
    assert "key2" in data["dict"]


def test_exclude_values_nested_model(get_instance):
    """Test that exclude_values works with nested models"""
    flat = get_instance(FlatModel)
    nested = get_instance(NestedModel, model_id=flat.id)
    nested.model = flat

    data = nested.to_dict(rules=("model",), exclude_values=(None,))

    assert "model" in data
    assert "null" not in data
    assert "null" not in data["model"]

    # Other fields should be present
    assert "id" in data["model"]
    assert "string" in data["model"]

    def test_exclude_values_class_level(get_instance):
        """Test class-level exclude_values works"""

        class ExcludeNullFlatModel(FlatModel):
            exclude_values = (None,)

        i = get_instance(ExcludeNullFlatModel)
        i.null = None
        i.string = "foobar"
        data = i.to_dict(only=("id", "null", "string"))
        assert "null" not in data
        assert "id" in data
        assert "string" in data and data["string"] == "foobar"

        # Nested model class level exclude_values
        class ExcludeNullNestedModel(NestedModel):
            exclude_values = (None,)

        nested = get_instance(ExcludeNullNestedModel)
        flat = get_instance(FlatModel)
        flat.null = None
        nested.model = flat

        data = nested.to_dict(rules=("model",))
        assert "model" in data
        assert "null" in data
        assert "null" not in data["model"]
