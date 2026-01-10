import inspect

from sqlalchemy import inspect as sql_inspect

# Cache for get_serializable_keys results,
# keyed by (class, serializable_keys_tuple, auto_serialize_properties)
_serializable_keys_cache: dict[tuple[type, tuple | None, bool], set[str]] = {}


def _get_cache_key(model_instance) -> tuple[type, tuple | None, bool]:
    """Generate cache key from model instance configuration.

    :param model_instance: Model instance to extract cache key from
    :return: Tuple of (class, serializable_keys_tuple, auto_serialize_properties)
    """
    cls = model_instance.__class__
    serializable_keys = (
        tuple(model_instance.serializable_keys) if model_instance.serializable_keys else None
    )
    auto_serialize_properties = bool(model_instance.auto_serialize_properties)
    return (cls, serializable_keys, auto_serialize_properties)


def get_sql_field_names(model_instance) -> set[str]:
    """:return:  set of sql fields names
    :raise:  sqlalchemy.exc.NoInspectionAvailable
    """
    inspector = sql_inspect(model_instance)
    return {a.key for a in inspector.mapper.attrs}


def get_property_field_names(model_instance) -> set[str]:
    """:return: set of field names defined as @property"""
    cls = model_instance.__class__
    return {name for name, member in inspect.getmembers(cls) if isinstance(member, property)}


def get_serializable_keys(model_instance) -> set[str]:
    """:return: set of keys available for serialization
    :raise:  sqlalchemy.exc.NoInspectionAvailable if model_instance is not an sqlalchemy mapper

    Results are cached by class and configuration
    (serializable_keys, auto_serialize_properties)
    rather than by instance, improving cache efficiency
    for collections of the same model type.
    """
    cache_key = _get_cache_key(model_instance)

    if cache_key in _serializable_keys_cache:
        return _serializable_keys_cache[cache_key]

    if model_instance.serializable_keys:
        result = set(model_instance.serializable_keys)
    else:
        result = get_sql_field_names(model_instance)

        if model_instance.auto_serialize_properties:
            result.update(get_property_field_names(model_instance))

    _serializable_keys_cache[cache_key] = result
    return result
