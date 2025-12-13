import pytest
from sqlalchemy.exc import NoInspectionAvailable

from sqlalchemy_serializer.lib.fields import get_sql_field_names

from .models import FlatModel


def test_get_sql_field_names__returns_result(get_instance):
    instance = get_instance(FlatModel)
    assert get_sql_field_names(instance) == {
        "id",
        "string",
        "date",
        "datetime",
        "time",
        "bool",
        "null",
        "uuid",
    }


class NonSqlInstance:
    a = 1

    def __init__(self) -> None:
        self.b = 2


@pytest.mark.parametrize("non_sql_instance", (object, [1, 2], dict(a=2), NonSqlInstance()))
def test_get_sql_field_names__raises_error(non_sql_instance):
    with pytest.raises(NoInspectionAvailable):
        get_sql_field_names(non_sql_instance)
