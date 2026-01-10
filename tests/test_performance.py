"""Performance tests for SQLAlchemy serializer using pytest-benchmark."""

from sqlalchemy_serializer.serializer import serialize_collection

from .models import FlatModel, NestedModel, RecursiveModel


def test_benchmark_flat_model_serialization(benchmark, get_instance):
    """Benchmark serialization of a flat model with standard fields."""
    model = get_instance(FlatModel)

    def serialize():
        return model.to_dict()

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert "id" in result


def test_benchmark_nested_model_serialization(benchmark, get_instance):
    """Benchmark serialization of a nested model with relationships."""
    flat = get_instance(FlatModel)
    nested = get_instance(NestedModel, model_id=flat.id)

    def serialize():
        return nested.to_dict()

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert "model" in result


def test_benchmark_collection_serialization(benchmark, get_instance):
    """Benchmark serialization of a collection of models."""
    models = [get_instance(FlatModel) for _ in range(10)]

    def serialize():
        return serialize_collection(models, only=("id", "string", "bool"))

    result = benchmark(serialize)
    assert isinstance(result, list)
    assert len(result) == 10


def test_benchmark_serialize_only_rules(benchmark, get_instance):
    """Benchmark serialization with serialize_only rules."""
    model = get_instance(FlatModel)

    def serialize():
        return model.to_dict(only=("id", "string", "datetime", "bool"))

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert len(result.keys()) == 4


def test_benchmark_serialize_rules(benchmark, get_instance):
    """Benchmark serialization with serialize_rules (greedy mode with additions)."""
    model = get_instance(FlatModel)

    def serialize():
        return model.to_dict(rules=("prop", "list", "dict"))

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert "prop" in result
    assert "list" in result
    assert "dict" in result


def test_benchmark_nested_serialize_only_rules(benchmark, get_instance):
    """Benchmark nested model serialization with serialize_only rules."""
    flat = get_instance(FlatModel)
    nested = get_instance(NestedModel, model_id=flat.id)

    def serialize():
        return nested.to_dict(only=("id", "model.id", "model.string", "model.bool"))

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert "model" in result


def test_benchmark_nested_serialize_rules(benchmark, get_instance):
    """Benchmark nested model serialization with serialize_rules."""
    flat = get_instance(FlatModel)
    nested = get_instance(NestedModel, model_id=flat.id)

    def serialize():
        return nested.to_dict(rules=("-id", "model.prop", "model.list", "model.dict"))

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert "model" in result


def test_benchmark_type_serialization_datetime(benchmark, get_instance):
    """Benchmark serialization of models with datetime/date/time fields."""
    model = get_instance(FlatModel)

    def serialize():
        return model.to_dict(only=("date", "datetime", "time"))

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert "date" in result
    assert "datetime" in result
    assert "time" in result


def test_benchmark_type_serialization_all_types(benchmark, get_instance):
    """Benchmark serialization of models with all supported types."""
    model = get_instance(FlatModel)

    def serialize():
        return model.to_dict(rules=("money", "prop_with_bytes", "uuid", "list", "dict", "set"))

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert "money" in result
    assert "uuid" in result


def test_benchmark_recursive_model_serialization(benchmark, get_instance):
    """Benchmark serialization of recursive models with depth limit."""
    parent = get_instance(RecursiveModel)
    child1 = get_instance(RecursiveModel, parent_id=parent.id, name="child1")
    _ = get_instance(RecursiveModel, parent_id=parent.id, name="child2")
    _ = get_instance(RecursiveModel, parent_id=child1.id, name="grandchild")

    def serialize():
        return parent.to_dict(rules=("children",), max_serialization_depth=2)

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert "children" in result


def test_benchmark_large_model_serialization(benchmark, get_instance):
    """Benchmark serialization of model with many fields and nested data."""
    model = get_instance(FlatModel)

    def serialize():
        return model.to_dict(
            rules=(
                "id",
                "string",
                "date",
                "datetime",
                "time",
                "bool",
                "null",
                "uuid",
                "prop",
                "prop_with_bytes",
                "list",
                "dict",
                "set",
                "money",
            )
        )

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert len(result.keys()) >= 10


def test_benchmark_auto_serialize_properties(benchmark, get_instance):
    """Benchmark serialization with auto_serialize_properties enabled."""

    class AutoPropModel(FlatModel):
        auto_serialize_properties = True

    model = get_instance(AutoPropModel)

    def serialize():
        return model.to_dict()

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert "prop" in result
    assert "prop_with_bytes" in result


def test_benchmark_custom_formats(benchmark, get_instance):
    """Benchmark serialization with custom date/datetime/time/decimal formats."""
    model = get_instance(FlatModel)

    def serialize():
        return model.to_dict(
            date_format="%Y/%m/%d",
            datetime_format="%Y/%m/%d %H:%M:%S",
            time_format="%H:%M:%S",
            decimal_format="{:.2f}",
            rules=("money",),
        )

    result = benchmark(serialize)
    assert isinstance(result, dict)
    assert "date" in result
    assert "money" in result


def test_benchmark_large_collection_serialization(benchmark, get_instance):
    """Benchmark serialization of a large collection to measure cache efficiency.

    This test demonstrates the performance benefit of class-based caching:
    - Serializing 1000 instances of the same model class should benefit from
      a single cache entry for get_serializable_keys() instead of 1000 entries.
    """
    # Create a large collection of the same model type
    models = [get_instance(FlatModel) for _ in range(1000)]

    def serialize():
        return serialize_collection(models, only=("id", "string", "bool", "datetime"))

    result = benchmark(serialize)
    assert isinstance(result, list)
    assert len(result) == 1000
    assert all(isinstance(item, dict) for item in result)
    assert all("id" in item for item in result)
