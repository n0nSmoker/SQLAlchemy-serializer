from .models import DATE, DATETIME, MONEY, TIME, ModernFlatModel, ModernNestedModel


def test_modern_flat_model_basic(get_instance):
    """Checks to_dict method of modern flat model with no predefined options"""
    i = get_instance(ModernFlatModel)
    data = i.to_dict()

    # Check SQLAlchemy fields
    assert "id" in data
    assert "string" in data and data["string"] == i.string
    assert "date_field" in data
    assert "time_field" in data
    assert "datetime_field" in data
    assert "bool_field" in data and data["bool_field"] == i.bool_field
    assert "null" in data and data["null"] is None
    assert "uuid" in data and str(i.uuid) == data["uuid"]

    # Check non-sql fields (not included in this case, need to be defined explicitly)
    assert "list" not in data
    assert "set" not in data
    assert "dict" not in data
    assert "prop" not in data
    assert "method" not in data
    assert "_protected_method" not in data
    assert "money" not in data


def test_modern_flat_model_with_properties(get_instance):
    "Checks to_dict method of modern flat model with automatic serialization of @properties"

    class AutoPropModernFlatModel(ModernFlatModel):
        auto_serialize_properties = True

    i = get_instance(AutoPropModernFlatModel)
    data = i.to_dict()

    # Check SQLAlchemy fields
    assert "id" in data
    assert "string" in data and data["string"] == i.string
    assert "date_field" in data
    assert "time_field" in data
    assert "datetime_field" in data
    assert "bool_field" in data and data["bool_field"] == i.bool_field
    assert "null" in data and data["null"] is None
    assert "uuid" in data and str(i.uuid) == data["uuid"]

    # Properties
    assert "prop" in data
    assert "prop_with_bytes" in data

    # Check non-sql fields
    assert "list" not in data
    assert "set" not in data
    assert "dict" not in data
    assert "method" not in data
    assert "_protected_method" not in data
    assert "money" not in data


def test_modern_models_formats(get_instance):
    """Check date/datetime/time/decimal default formats for modern models"""
    i = get_instance(ModernFlatModel)

    # Default formats
    d_format = i.date_format
    dt_format = i.datetime_format
    t_format = i.time_format
    decimal_format = i.decimal_format

    # Include non-SQL field to check decimal_format and bytes
    data = i.to_dict(rules=("money", "prop_with_bytes"))

    assert "date_field" in data
    assert data["date_field"] == DATE.strftime(d_format)
    assert "datetime_field" in data
    assert data["datetime_field"] == DATETIME.strftime(dt_format)
    assert "time_field" in data
    assert data["time_field"] == TIME.strftime(t_format)

    assert "money" in data
    assert data["money"] == decimal_format.format(MONEY)

    assert "prop_with_bytes" in data
    assert data["prop_with_bytes"] == i.prop_with_bytes.decode()


def test_modern_nested_model(get_instance):
    """Test relationship serialization with modern nested model"""
    flat = get_instance(ModernFlatModel)
    nested = get_instance(ModernNestedModel, model_id=flat.id)

    # Test basic serialization
    data = nested.to_dict()
    assert "id" in data
    assert "string" in data
    assert "model_id" in data
    assert data["model_id"] == flat.id

    # Test relationship serialization
    data_with_relation = nested.to_dict(rules=("model",))
    assert "model" in data_with_relation
    assert isinstance(data_with_relation["model"], dict)
    assert data_with_relation["model"]["id"] == flat.id
    assert data_with_relation["model"]["string"] == flat.string


def test_modern_models_rules(get_instance):
    """Test rules and only parameters with modern models"""
    i = get_instance(ModernFlatModel)

    # Test rules parameter
    data = i.to_dict(rules=("-id", "prop", "method"))
    assert "id" not in data
    assert "string" in data
    assert "prop" in data
    assert data["prop"] == i.prop
    assert "method" in data
    assert data["method"] == i.method()

    # Test only parameter
    data_only = i.to_dict(only=("id", "string", "prop"))
    assert "id" in data_only
    assert "string" in data_only
    assert "prop" in data_only
    assert len(data_only.keys()) == 3
