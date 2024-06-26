import functools
import typing as t
import inspect
from sqlalchemy import inspect as sql_inspect


def get_sql_field_names(model_instance) -> t.Set[str]:
    """
    :return:  set of sql fields names
    :raise:  sqlalchemy.exc.NoInspectionAvailable
    """
    inspector = sql_inspect(model_instance)
    return {a.key for a in inspector.mapper.attrs}


def get_property_field_names(model_instance) -> t.Set[str]:
    """
    :return: set of field names defined as @property
    """
    cls = model_instance.__class__
    return {
        name for name, member in inspect.getmembers(cls) if isinstance(member, property)
    }


@functools.lru_cache
def get_serializable_keys(model_instance) -> t.Set[str]:
    """
    :return: set of keys available for serialization
    :raise:  sqlalchemy.exc.NoInspectionAvailable if model_instance is not an sqlalchemy mapper
    """
    if model_instance.serializable_keys:
        result = set(model_instance.serializable_keys)

    else:
        result = get_sql_field_names(model_instance)

        if model_instance.auto_serialize_properties:
            result.update(get_property_field_names(model_instance))

    return result
