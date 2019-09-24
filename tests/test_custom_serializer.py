from .models import (CustomSerializerModel, DATETIME, TIME, DATE, MONEY,
                     CUSTOM_TZINFO,
                     CUSTOM_DATE_FORMAT, CUSTOM_TIME_FORMAT, CUSTOM_DATE_TIME_FORMAT, CUSTOM_DECIMAL_FORMAT,
                     CUSTOM_STR_VALUE)


def test_tzinfo_set_in_serializer(get_instance):
    """
    Checks how serializer applies tzinfo for datetime objects
    :param get_instance:
    :return:
    """
    i = get_instance(CustomSerializerModel)
    data = i.to_dict()

    # Check time/date formats
    assert 'date' in data
    assert data['date'] == DATE.strftime(CUSTOM_DATE_FORMAT)
    assert 'datetime' in data
    assert 'time' in data
    assert data['time'] == TIME.strftime(CUSTOM_TIME_FORMAT)

    assert 'money' in data
    assert data['money'] == CUSTOM_DECIMAL_FORMAT.format(MONEY)

    # Timezone info affects only datetime objects
    assert data['datetime'] == DATETIME.astimezone(CUSTOM_TZINFO).strftime(CUSTOM_DATE_TIME_FORMAT)

    # Check other fields
    assert 'id' in data
    assert 'string' in data
    assert 'bool' in data


def test_add_custom_serialization_types(get_instance):
    """
    Checks custom type serializers
    :param get_instance:
    :return:
    """
    i = get_instance(CustomSerializerModel)
    data = i.to_dict()

    assert 'string' in data
    assert data['string'] == CUSTOM_STR_VALUE
    assert 'id' in data
    assert data['id'] == i.id

    # Redefine serializer
    CustomSerializerModel.serialize_types = (
        (str, lambda x: 'New value'),
        (int, lambda x: x+1)
    )
    i = get_instance(CustomSerializerModel)
    data = i.to_dict()

    assert 'string' in data
    assert data['string'] == 'New value'
    assert 'id' in data
    assert data['id'] == i.id + 1
