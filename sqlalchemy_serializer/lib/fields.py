import typing as t
from sqlalchemy import inspect as sql_inspect


def get_sql_field_names(model_instance) -> t.Iterable[str]:
    """
    Returns a set of sql fields names
    or rises sqlalchemy.exc.NoInspectionAvailable
    """
    inspector = sql_inspect(model_instance)
    return {a.key for a in inspector.mapper.attrs}
